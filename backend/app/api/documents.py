import os
import uuid
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from app.config import settings
from app.database import db_manager
from app.dependencies import get_current_user
from app.models.user import UserInDB
from app.schemas.document import DocumentListResponse, DocumentResponse, DocumentStatusResponse
from app.services.chunking_service import chunking_service
from app.services.embedding_service import embedding_service
from app.services.pdf_service import PDFProcessingError, pdf_service
from app.services.vector_store import get_vector_store

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Uploads, validates, extracts, chunks, and indexes a PDF document for the authenticated user.
    """
    # 1. Basic filename validation
    filename = os.path.basename(file.filename or "uploaded.pdf")
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file format. Only PDF files (.pdf) are permitted."
        )

    # 2. Read bytes safely
    try:
        content = await file.read()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not read uploaded file: {str(e)}"
        )

    # 3. Content and structural validation
    try:
        pdf_service.validate_file(content, filename)
    except PDFProcessingError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    # 4. Extract text page by page
    try:
        pages_data = pdf_service.extract_text(content)
    except PDFProcessingError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )

    doc_id = str(uuid.uuid4())
    file_hash = pdf_service.compute_sha256(content)
    now = datetime.now(timezone.utc)

    # 5. Check if identical document already uploaded by this user
    duplicate = db_manager.documents.find_one({"owner_id": current_user.id, "file_hash": file_hash})
    if duplicate:
        # Check if status is indexed
        if duplicate.get("status") == "indexed":
            return DocumentResponse(
                id=duplicate["id"],
                owner_id=duplicate["owner_id"],
                filename=duplicate["filename"],
                file_size_bytes=duplicate["file_size_bytes"],
                page_count=duplicate["page_count"],
                status="indexed",
                chunk_count=duplicate["chunk_count"],
                error_message=None,
                uploaded_at=duplicate["uploaded_at"] if isinstance(duplicate["uploaded_at"], datetime) else datetime.fromisoformat(duplicate["uploaded_at"])
            )

    # 6. Save PDF file safely
    file_path = pdf_service.save_file(doc_id, content)

    # 7. Create initial document record
    doc_record = {
        "_id": doc_id,
        "id": doc_id,
        "owner_id": current_user.id,
        "filename": filename,
        "safe_storage_name": f"{doc_id}.pdf",
        "file_path": file_path,
        "file_size_bytes": len(content),
        "file_hash": file_hash,
        "page_count": len(pages_data),
        "status": "processing",
        "error_message": None,
        "chunk_count": 0,
        "uploaded_at": now
    }
    db_manager.documents.insert_one(doc_record)

    # 8. Chunking & Indexing Pipeline
    vector_store = get_vector_store()
    try:
        chunks = chunking_service.chunk_document(
            document_id=doc_id,
            owner_id=current_user.id,
            filename=filename,
            pages_data=pages_data
        )

        if not chunks:
            raise PDFProcessingError("No readable content could be extracted into chunks.")

        # Extract text strings for embedding
        chunk_texts = [c["text"] for c in chunks]
        embeddings = embedding_service.embed_texts(chunk_texts)

        # Store in vector store
        vector_store.insert_chunks(chunks, embeddings)

        # Update status to indexed
        db_manager.documents.update_one(
            {"id": doc_id},
            {"$set": {"status": "indexed", "chunk_count": len(chunks)}}
        )

        return DocumentResponse(
            id=doc_id,
            owner_id=current_user.id,
            filename=filename,
            file_size_bytes=len(content),
            page_count=len(pages_data),
            status="indexed",
            chunk_count=len(chunks),
            error_message=None,
            uploaded_at=now
        )
    except Exception as e:
        # Cleanup partially saved data on failure
        db_manager.documents.update_one(
            {"id": doc_id},
            {"$set": {"status": "failed", "error_message": str(e)}}
        )
        vector_store.delete_document_chunks(doc_id, current_user.id)
        pdf_service.delete_file(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process and index document: {str(e)}"
        )


@router.get("", response_model=DocumentListResponse)
async def list_documents(current_user: UserInDB = Depends(get_current_user)):
    """
    Returns all indexed documents belonging to the current user.
    """
    docs_cursor = db_manager.documents.find({"owner_id": current_user.id})
    documents = []
    for d in docs_cursor:
        uploaded_at = d.get("uploaded_at")
        if isinstance(uploaded_at, str):
            uploaded_at = datetime.fromisoformat(uploaded_at)
        elif not uploaded_at:
            uploaded_at = datetime.now(timezone.utc)

        documents.append(DocumentResponse(
            id=d["id"],
            owner_id=d["owner_id"],
            filename=d["filename"],
            file_size_bytes=d.get("file_size_bytes", 0),
            page_count=d.get("page_count", 0),
            status=d.get("status", "unknown"),
            chunk_count=d.get("chunk_count", 0),
            error_message=d.get("error_message"),
            uploaded_at=uploaded_at
        ))

    # Sort descending by upload date
    documents.sort(key=lambda x: x.uploaded_at, reverse=True)
    return DocumentListResponse(documents=documents, total=len(documents))


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: str, current_user: UserInDB = Depends(get_current_user)):
    """
    Retrieves metadata for a specific document owned by the user.
    """
    doc = db_manager.documents.find_one({"id": document_id, "owner_id": current_user.id})
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or you do not have permission to access it."
        )

    uploaded_at = doc.get("uploaded_at")
    if isinstance(uploaded_at, str):
        uploaded_at = datetime.fromisoformat(uploaded_at)
    elif not uploaded_at:
        uploaded_at = datetime.now(timezone.utc)

    return DocumentResponse(
        id=doc["id"],
        owner_id=doc["owner_id"],
        filename=doc["filename"],
        file_size_bytes=doc.get("file_size_bytes", 0),
        page_count=doc.get("page_count", 0),
        status=doc.get("status", "unknown"),
        chunk_count=doc.get("chunk_count", 0),
        error_message=doc.get("error_message"),
        uploaded_at=uploaded_at
    )


@router.get("/{document_id}/status", response_model=DocumentStatusResponse)
async def get_document_status(document_id: str, current_user: UserInDB = Depends(get_current_user)):
    """
    Lightweight status polling endpoint for document processing.
    """
    doc = db_manager.documents.find_one({"id": document_id, "owner_id": current_user.id})
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found."
        )

    return DocumentStatusResponse(
        id=doc["id"],
        status=doc.get("status", "unknown"),
        page_count=doc.get("page_count", 0),
        chunk_count=doc.get("chunk_count", 0),
        error_message=doc.get("error_message")
    )


@router.delete("/{document_id}", status_code=status.HTTP_200_OK)
async def delete_document(document_id: str, current_user: UserInDB = Depends(get_current_user)):
    """
    Permanently deletes a document, its vector index chunks, and its filesystem storage.
    Enforces user ownership.
    """
    doc = db_manager.documents.find_one({"id": document_id, "owner_id": current_user.id})
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or you do not have permission to delete it."
        )

    # 1. Delete vector store chunks
    vector_store = get_vector_store()
    vector_store.delete_document_chunks(document_id, current_user.id)

    # 2. Delete file from storage
    if "file_path" in doc:
        pdf_service.delete_file(doc["file_path"])

    # 3. Delete document from database
    db_manager.documents.delete_one({"id": document_id, "owner_id": current_user.id})

    return {"message": "Document and associated vector chunks deleted successfully.", "document_id": document_id}
