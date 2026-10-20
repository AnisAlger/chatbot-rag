from app.services.embedding_service import embedding_service
from app.services.vector_store import LocalVectorStore


def test_vector_store_insert_and_user_isolation(tmp_path):
    store = LocalVectorStore(store_path=str(tmp_path / "vec_test"))

    # User A chunks
    chunks_a = [
        {"chunk_id": "c1", "document_id": "doc_a", "owner_id": "user_a", "filename": "docA.pdf", "page_number": 1, "text": "Financial projections for Q3 revenue growth."},
        {"chunk_id": "c2", "document_id": "doc_a", "owner_id": "user_a", "filename": "docA.pdf", "page_number": 2, "text": "Marketing budget and expenses for advertisement campaigns."}
    ]
    texts_a = [c["text"] for c in chunks_a]
    embeddings_a = embedding_service.embed_texts(texts_a)
    store.insert_chunks(chunks_a, embeddings_a)

    # User B chunks
    chunks_b = [
        {"chunk_id": "c3", "document_id": "doc_b", "owner_id": "user_b", "filename": "docB.pdf", "page_number": 1, "text": "Confidential medical clinical trial records for oncology."}
    ]
    texts_b = [c["text"] for c in chunks_b]
    embeddings_b = embedding_service.embed_texts(texts_b)
    store.insert_chunks(chunks_b, embeddings_b)

    query = "revenue projections"
    q_vec = embedding_service.embed_query(query)

    # Search as User A -> Should only return User A's chunks
    results_a = store.search(q_vec, owner_id="user_a", top_k=5)
    assert len(results_a) > 0
    for res in results_a:
        assert res["owner_id"] == "user_a"
        assert res["document_id"] == "doc_a"

    # Search as User B with the same query -> Must NOT return User A's financial chunks
    results_b = store.search(q_vec, owner_id="user_b", top_k=5)
    for res in results_b:
        assert res["owner_id"] == "user_b"

    # Verify deletion
    deleted = store.delete_document_chunks("doc_a", "user_a")
    assert deleted == 2
    post_del_results = store.search(q_vec, owner_id="user_a", top_k=5)
    assert len(post_del_results) == 0
