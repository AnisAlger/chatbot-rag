import io
from tests.conftest import create_pdf_bytes_with_text


def test_full_rag_workflow_with_citations_and_isolation(client, test_user, second_user):
    # 1. User A uploads a valid PDF document
    doc_text = "The serverless architecture reduces operational latency to under 50 milliseconds while cutting cloud costs by 40 percent."
    pdf_bytes = create_pdf_bytes_with_text(doc_text)

    upload_resp = client.post(
        "/documents/upload",
        headers=test_user["headers"],
        files={"file": ("architecture_report.pdf", pdf_bytes, "application/pdf")}
    )
    assert upload_resp.status_code == 201
    doc_data = upload_resp.json()
    doc_id = doc_data["id"]
    assert doc_data["status"] == "indexed"
    assert doc_data["chunk_count"] >= 1
    assert doc_data["filename"] == "architecture_report.pdf"

    # 2. Verify User A can list documents
    list_resp = client.get("/documents", headers=test_user["headers"])
    assert list_resp.status_code == 200
    assert any(d["id"] == doc_id for d in list_resp.json()["documents"])

    # 3. Security check: User B cannot access User A's document
    b_get_doc = client.get(f"/documents/{doc_id}", headers=second_user["headers"])
    assert b_get_doc.status_code == 404

    # 4. Create a conversation for User A
    conv_resp = client.post(
        "/conversations",
        headers=test_user["headers"],
        json={"title": "Cloud Latency Inquiry", "selected_document_ids": [doc_id]}
    )
    assert conv_resp.status_code == 201
    conv_id = conv_resp.json()["id"]

    # 5. Security check: User B cannot access User A's conversation
    b_conv_access = client.get(f"/conversations/{conv_id}", headers=second_user["headers"])
    assert b_conv_access.status_code == 404

    # 6. User A asks a grounded question
    msg_resp = client.post(
        f"/conversations/{conv_id}/messages",
        headers=test_user["headers"],
        json={"content": "What is the operational latency reduction?"}
    )
    assert msg_resp.status_code == 200
    ans_data = msg_resp.json()
    assert "answer" in ans_data
    assert "citations" in ans_data
    assert len(ans_data["citations"]) >= 1

    # Verify citation integrity
    cit = ans_data["citations"][0]
    assert cit["document_id"] == doc_id
    assert cit["filename"] == "architecture_report.pdf"
    assert cit["page"] == 1
    assert "latency" in cit["excerpt"].lower() or "50 milliseconds" in cit["excerpt"].lower()
    assert ans_data["retrieval"]["chunks_used"] >= 1

    # 7. Check message history in conversation
    conv_detail = client.get(f"/conversations/{conv_id}", headers=test_user["headers"])
    assert conv_detail.status_code == 200
    msgs = conv_detail.json()["messages"]
    assert len(msgs) == 2  # 1 user + 1 assistant

    # 8. Delete document by User A
    del_resp = client.delete(f"/documents/{doc_id}", headers=test_user["headers"])
    assert del_resp.status_code == 200

    # Verify document no longer exists
    get_del = client.get(f"/documents/{doc_id}", headers=test_user["headers"])
    assert get_del.status_code == 404
