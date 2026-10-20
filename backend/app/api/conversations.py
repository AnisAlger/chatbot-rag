import uuid
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from app.database import db_manager
from app.dependencies import get_current_user
from app.models.user import UserInDB
from app.schemas.conversation import (
    ChatAnswerResponse,
    Citation,
    ConversationDetailResponse,
    ConversationSummaryResponse,
    CreateConversationRequest,
    MessageResponse,
    RetrievalMeta,
    SendMessageRequest,
    UpdateConversationRequest,
)
from app.services.rag_service import rag_service

router = APIRouter(prefix="/conversations", tags=["Conversations & Chat"])


@router.post("", response_model=ConversationDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    request: CreateConversationRequest,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Creates a new conversation session associated with the user and optional selected documents.
    """
    # Verify that requested documents belong to this user
    doc_ids = []
    if request.selected_document_ids:
        user_docs = list(db_manager.documents.find({
            "owner_id": current_user.id,
            "id": {"$in": request.selected_document_ids}
        }))
        doc_ids = [d["id"] for d in user_docs]

    conv_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    conv_record = {
        "_id": conv_id,
        "id": conv_id,
        "owner_id": current_user.id,
        "title": request.title.strip() if request.title else "New Conversation",
        "selected_document_ids": doc_ids,
        "created_at": now,
        "updated_at": now
    }
    db_manager.conversations.insert_one(conv_record)

    return ConversationDetailResponse(
        id=conv_id,
        title=conv_record["title"],
        selected_document_ids=doc_ids,
        created_at=now,
        updated_at=now,
        messages=[]
    )


@router.get("", response_model=List[ConversationSummaryResponse])
async def list_conversations(current_user: UserInDB = Depends(get_current_user)):
    """
    Returns all conversations belonging to the authenticated user.
    """
    convs_cursor = db_manager.conversations.find({"owner_id": current_user.id})
    summaries = []
    for c in convs_cursor:
        c_id = c["id"]
        msg_count = db_manager.messages.count_documents({"conversation_id": c_id})

        created_at = c.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        elif not created_at:
            created_at = datetime.now(timezone.utc)

        updated_at = c.get("updated_at")
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)
        elif not updated_at:
            updated_at = datetime.now(timezone.utc)

        summaries.append(ConversationSummaryResponse(
            id=c_id,
            title=c.get("title", "Conversation"),
            selected_document_ids=c.get("selected_document_ids", []),
            created_at=created_at,
            updated_at=updated_at,
            message_count=msg_count
        ))

    summaries.sort(key=lambda x: x.updated_at, reverse=True)
    return summaries


@router.get("/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(conversation_id: str, current_user: UserInDB = Depends(get_current_user)):
    """
    Retrieves full conversation details including all message history.
    Enforces user ownership.
    """
    conv = db_manager.conversations.find_one({"id": conversation_id, "owner_id": current_user.id})
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found or access denied."
        )

    # Fetch messages
    msg_cursor = db_manager.messages.find({"conversation_id": conversation_id})
    messages: List[MessageResponse] = []
    for m in msg_cursor:
        m_created = m.get("created_at")
        if isinstance(m_created, str):
            m_created = datetime.fromisoformat(m_created)
        elif not m_created:
            m_created = datetime.now(timezone.utc)

        raw_cits = m.get("citations") or []
        citations = [Citation(**c) if isinstance(c, dict) else c for c in raw_cits]
        retrieval_meta = RetrievalMeta(**m["retrieval_meta"]) if m.get("retrieval_meta") else None

        messages.append(MessageResponse(
            id=m["id"],
            conversation_id=m["conversation_id"],
            role=m["role"],
            content=m["content"],
            citations=citations if citations else None,
            retrieval_meta=retrieval_meta,
            created_at=m_created
        ))

    messages.sort(key=lambda x: x.created_at)

    created_at = conv.get("created_at")
    if isinstance(created_at, str):
        created_at = datetime.fromisoformat(created_at)
    elif not created_at:
        created_at = datetime.now(timezone.utc)

    updated_at = conv.get("updated_at")
    if isinstance(updated_at, str):
        updated_at = datetime.fromisoformat(updated_at)
    elif not updated_at:
        updated_at = datetime.now(timezone.utc)

    return ConversationDetailResponse(
        id=conv["id"],
        title=conv.get("title", "Conversation"),
        selected_document_ids=conv.get("selected_document_ids", []),
        created_at=created_at,
        updated_at=updated_at,
        messages=messages
    )


@router.patch("/{conversation_id}", response_model=ConversationSummaryResponse)
async def update_conversation(
    conversation_id: str,
    request: UpdateConversationRequest,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Renames a conversation or updates its selected document bindings.
    """
    conv = db_manager.conversations.find_one({"id": conversation_id, "owner_id": current_user.id})
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found."
        )

    updates = {"updated_at": datetime.now(timezone.utc)}
    if request.title is not None and request.title.strip():
        updates["title"] = request.title.strip()

    if request.selected_document_ids is not None:
        user_docs = list(db_manager.documents.find({
            "owner_id": current_user.id,
            "id": {"$in": request.selected_document_ids}
        }))
        updates["selected_document_ids"] = [d["id"] for d in user_docs]

    db_manager.conversations.update_one({"id": conversation_id}, {"$set": updates})
    updated_conv = db_manager.conversations.find_one({"id": conversation_id})

    msg_count = db_manager.messages.count_documents({"conversation_id": conversation_id})
    return ConversationSummaryResponse(
        id=updated_conv["id"],
        title=updated_conv.get("title", "Conversation"),
        selected_document_ids=updated_conv.get("selected_document_ids", []),
        created_at=updated_conv.get("created_at") if isinstance(updated_conv.get("created_at"), datetime) else datetime.fromisoformat(str(updated_conv.get("created_at"))),
        updated_at=updated_conv.get("updated_at") if isinstance(updated_conv.get("updated_at"), datetime) else datetime.fromisoformat(str(updated_conv.get("updated_at"))),
        message_count=msg_count
    )


@router.delete("/{conversation_id}", status_code=status.HTTP_200_OK)
async def delete_conversation(conversation_id: str, current_user: UserInDB = Depends(get_current_user)):
    """
    Deletes a conversation and its messages. Enforces ownership.
    """
    conv = db_manager.conversations.find_one({"id": conversation_id, "owner_id": current_user.id})
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found or access denied."
        )

    db_manager.messages.delete_many({"conversation_id": conversation_id})
    db_manager.conversations.delete_one({"id": conversation_id, "owner_id": current_user.id})

    return {"message": "Conversation deleted successfully.", "conversation_id": conversation_id}


@router.post("/{conversation_id}/messages", response_model=ChatAnswerResponse)
async def send_message(
    conversation_id: str,
    request: SendMessageRequest,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Sends a message in the conversation, invokes the RAG pipeline,
    and returns the grounded answer with verified source citations.
    """
    conv = db_manager.conversations.find_one({"id": conversation_id, "owner_id": current_user.id})
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found or access denied."
        )

    # Determine document filtering
    if request.selected_document_ids is not None:
        target_doc_ids = request.selected_document_ids
    else:
        target_doc_ids = conv.get("selected_document_ids", [])

    # Validate that target doc ids belong to the current user
    if target_doc_ids:
        user_valid_docs = list(db_manager.documents.find({
            "owner_id": current_user.id,
            "id": {"$in": target_doc_ids}
        }))
        target_doc_ids = [d["id"] for d in user_valid_docs]

    now = datetime.now(timezone.utc)
    user_msg_id = str(uuid.uuid4())

    # Save user message
    user_msg_record = {
        "_id": user_msg_id,
        "id": user_msg_id,
        "conversation_id": conversation_id,
        "owner_id": current_user.id,
        "role": "user",
        "content": request.content.strip(),
        "created_at": now
    }
    db_manager.messages.insert_one(user_msg_record)

    # Fetch recent conversation history
    past_messages = list(db_manager.messages.find({"conversation_id": conversation_id}))
    history = [{"role": m["role"], "content": m["content"]} for m in past_messages if m["id"] != user_msg_id]

    # Execute RAG
    answer, citations, retrieval_meta = rag_service.answer_question(
        question=request.content.strip(),
        owner_id=current_user.id,
        conversation_history=history,
        selected_document_ids=target_doc_ids if target_doc_ids else None
    )

    # Save assistant message
    asst_msg_id = str(uuid.uuid4())
    asst_now = datetime.now(timezone.utc)
    citations_data = [c.model_dump() for c in citations]

    asst_msg_record = {
        "_id": asst_msg_id,
        "id": asst_msg_id,
        "conversation_id": conversation_id,
        "owner_id": current_user.id,
        "role": "assistant",
        "content": answer,
        "citations": citations_data,
        "retrieval_meta": retrieval_meta.model_dump(),
        "created_at": asst_now
    }
    db_manager.messages.insert_one(asst_msg_record)

    # If first message, auto-title conversation from question
    if conv.get("title") == "New Conversation":
        new_title = request.content.strip()[:40]
        if len(request.content.strip()) > 40:
            new_title += "..."
        db_manager.conversations.update_one(
            {"id": conversation_id},
            {"$set": {"title": new_title, "updated_at": asst_now}}
        )
    else:
        db_manager.conversations.update_one(
            {"id": conversation_id},
            {"$set": {"updated_at": asst_now}}
        )

    return ChatAnswerResponse(
        conversation_id=conversation_id,
        answer=answer,
        citations=citations,
        retrieval=retrieval_meta
    )
