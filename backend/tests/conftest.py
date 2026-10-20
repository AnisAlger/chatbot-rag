import io
import os
import shutil
import tempfile
import uuid
import pytest
from fastapi.testclient import TestClient
import pypdf
from app.config import settings
from app.database import db_manager, InMemoryDatabase
from app.main import app
from app.services.embedding_service import embedding_service, LocalMockEmbeddingProvider
from app.services.pdf_service import pdf_service
from app.services.vector_store import LocalVectorStore, _vector_store
import app.services.vector_store as vs_module


@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch, tmp_path):
    """
    Sets up an isolated in-memory test database, temporary upload and vector folders,
    and mock embedding provider for fast, deterministic, credential-free testing.
    """
    # 1. Prevent lifespan from connecting to external MongoDB during unit tests
    test_db = InMemoryDatabase(f"test_rag_db_{uuid.uuid4().hex[:8]}")
    monkeypatch.setattr(db_manager, "connect", lambda: None)
    db_manager._db = test_db
    db_manager._is_fallback = True

    # 2. Point uploads and vector stores to temp dir
    test_upload_dir = tmp_path / "uploads"
    test_vector_dir = tmp_path / "vector_store"
    test_upload_dir.mkdir(parents=True, exist_ok=True)
    test_vector_dir.mkdir(parents=True, exist_ok=True)

    pdf_service.upload_dir = test_upload_dir
    local_store = LocalVectorStore(store_path=str(test_vector_dir))
    vs_module._vector_store = local_store

    # 3. Use deterministic mock embeddings
    embedding_service.set_provider(LocalMockEmbeddingProvider(dim=64))

    yield

    # Cleanup
    if test_upload_dir.exists():
        shutil.rmtree(str(test_upload_dir), ignore_errors=True)
    if test_vector_dir.exists():
        shutil.rmtree(str(test_vector_dir), ignore_errors=True)


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def test_user(client):
    """Creates a standard test user and returns user data and auth header."""
    uid = uuid.uuid4().hex[:6]
    raw_pwd = "StrongPassword123!"
    user_payload = {
        "email": f"alice_{uid}@example.com",
        "password": raw_pwd,
        "full_name": "Alice Tester"
    }
    resp = client.post("/auth/register", json=user_payload)
    data = resp.json()
    token = data["access_token"]
    user = data["user"]
    headers = {"Authorization": f"Bearer {token}"}
    return {"user": user, "token": token, "password": raw_pwd, "headers": headers}


@pytest.fixture
def second_user(client):
    """Creates a second user for cross-user isolation tests."""
    uid = uuid.uuid4().hex[:6]
    user_payload = {
        "email": f"bob_{uid}@example.com",
        "password": "StrongPassword456!",
        "full_name": "Bob Tester"
    }
    resp = client.post("/auth/register", json=user_payload)
    data = resp.json()
    return {"user": data["user"], "token": data["access_token"], "headers": {"Authorization": f"Bearer {data['access_token']}"}}


def create_pdf_bytes_with_text(text: str, num_pages: int = 1) -> bytes:
    """Helper to generate a valid PDF byte string with extractable text."""
    pdf_content = (
        b"%PDF-1.4\n"
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n"
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj\n"
        b"4 0 obj << /Length " + str(len(text) + 50).encode("ascii") + b" >>\n"
        b"stream\n"
        b"BT\n"
        b"/F1 12 Tf\n"
        b"72 712 Td\n"
        b"(" + text.replace("(", "").replace(")", "").encode("latin-1", "replace") + b") Tj\n"
        b"ET\n"
        b"endstream\n"
        b"endobj\n"
        b"5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n"
        b"xref\n"
        b"0 6\n"
        b"0000000000 65535 f \n"
        b"0000000010 00000 n \n"
        b"0000000060 00000 n \n"
        b"0000000117 00000 n \n"
        b"0000000240 00000 n \n"
        b"0000000350 00000 n \n"
        b"trailer << /Size 6 /Root 1 0 R >>\n"
        b"startxref\n"
        b"420\n"
        b"%%EOF\n"
    )
    return pdf_content
