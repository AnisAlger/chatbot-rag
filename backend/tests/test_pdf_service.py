import io
import pytest
from app.services.pdf_service import PDFProcessingError, pdf_service
from tests.conftest import create_pdf_bytes_with_text


def test_pdf_validation_empty_bytes():
    with pytest.raises(PDFProcessingError) as exc_info:
        pdf_service.validate_file(b"", "empty.pdf")
    assert "empty" in str(exc_info.value).lower()


def test_pdf_validation_not_pdf():
    with pytest.raises(PDFProcessingError) as exc_info:
        pdf_service.validate_file(b"This is just raw text, not a PDF document.", "test.pdf")
    assert "not a valid pdf" in str(exc_info.value).lower()


def test_pdf_validation_malformed_pdf():
    with pytest.raises(PDFProcessingError) as exc_info:
        pdf_service.validate_file(b"%PDF-1.4\ncorrupted content without xref or trailer", "bad.pdf")
    assert "malformed or corrupted" in str(exc_info.value).lower()


def test_pdf_scanned_ocr_detection():
    # PDF with blank page (no text content)
    import pypdf
    writer = pypdf.PdfWriter()
    writer.add_blank_page(width=100, height=100)
    buf = io.BytesIO()
    writer.write(buf)
    blank_pdf_bytes = buf.getvalue()

    with pytest.raises(PDFProcessingError) as exc_info:
        pdf_service.extract_text(blank_pdf_bytes)
    assert "ocr" in str(exc_info.value).lower()


def test_pdf_valid_extraction():
    text_content = "This is a confidential annual report covering operational growth and financial statements."
    pdf_bytes = create_pdf_bytes_with_text(text_content)
    
    pdf_service.validate_file(pdf_bytes, "report.pdf")
    pages = pdf_service.extract_text(pdf_bytes)
    assert len(pages) == 1
    assert "confidential annual report" in pages[0]["text"]
    assert pages[0]["page_number"] == 1


def test_pdf_sha256_deterministic():
    content = b"%PDF-1.4 sample content"
    hash1 = pdf_service.compute_sha256(content)
    hash2 = pdf_service.compute_sha256(content)
    assert hash1 == hash2
    assert len(hash1) == 64
