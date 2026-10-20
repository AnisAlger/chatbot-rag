from app.services.chunking_service import ChunkingService


def test_chunking_short_text():
    service = ChunkingService(chunk_size_tokens=100, overlap_tokens=20)
    pages_data = [
        {"page_number": 1, "text": "Short introductory paragraph for testing."}
    ]
    chunks = service.chunk_document(
        document_id="doc_123",
        owner_id="user_abc",
        filename="notes.pdf",
        pages_data=pages_data
    )

    assert len(chunks) == 1
    c = chunks[0]
    assert c["chunk_id"] == "doc_123_c0"
    assert c["document_id"] == "doc_123"
    assert c["owner_id"] == "user_abc"
    assert c["filename"] == "notes.pdf"
    assert c["page_number"] == 1
    assert "Short introductory paragraph" in c["text"]


def test_chunking_multi_page_and_empty_handling():
    service = ChunkingService(chunk_size_tokens=50, overlap_tokens=10)
    pages_data = [
        {"page_number": 1, "text": "Page one text content with substantial words to make it chunkable."},
        {"page_number": 2, "text": ""},  # empty page
        {"page_number": 3, "text": "Page three text content with distinct information."}
    ]
    chunks = service.chunk_document(
        document_id="doc_456",
        owner_id="user_xyz",
        filename="guide.pdf",
        pages_data=pages_data
    )

    assert len(chunks) >= 2
    # Ensure no chunks were generated from empty page 2
    page_numbers = [c["page_number"] for c in chunks]
    assert 1 in page_numbers
    assert 2 not in page_numbers
    assert 3 in page_numbers
