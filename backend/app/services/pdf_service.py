import hashlib
import io
import os
import re
from pathlib import Path
from typing import Any, Dict, List
import pypdf
from app.config import settings


class PDFProcessingError(Exception):
    """Custom exception raised for PDF validation and extraction failures."""
    pass


class PDFService:
    """
    Handles PDF validation, safe storage, and page-by-page text extraction.
    Enforces file size limits, PDF structural checks, and OCR requirement detection.
    """

    def __init__(self, upload_dir: str = settings.UPLOAD_DIR, max_bytes: int = settings.max_upload_bytes):
        self.upload_dir = Path(upload_dir)
        self.max_bytes = max_bytes
        self.max_pages = 250  # reasonable safety ceiling
        self._ensure_upload_dir()

    def _ensure_upload_dir(self):
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def compute_sha256(self, file_bytes: bytes) -> str:
        return hashlib.sha256(file_bytes).hexdigest()

    def validate_file(self, file_bytes: bytes, filename: str) -> None:
        """
        Validates raw bytes against PDF format rules, size constraints, and encryption.
        """
        if not file_bytes or len(file_bytes) == 0:
            raise PDFProcessingError("Uploaded file is empty.")

        if len(file_bytes) > self.max_bytes:
            raise PDFProcessingError(
                f"File size ({len(file_bytes) / (1024*1024):.1f} MB) exceeds maximum allowed limit of {settings.MAX_UPLOAD_MB} MB."
            )

        # Check PDF magic bytes (%PDF-)
        if not file_bytes.startswith(b"%PDF-"):
            # Some PDFs have minimal leading whitespace/BOM, check first 1024 bytes
            if b"%PDF-" not in file_bytes[:1024]:
                raise PDFProcessingError("Invalid file content: The file is not a valid PDF document.")

        # Validate with pypdf
        try:
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        except Exception as e:
            raise PDFProcessingError(f"Malformed or corrupted PDF file: {str(e)}")

        if reader.is_encrypted:
            raise PDFProcessingError("Encrypted or password-protected PDFs are not supported. Please remove the password protection and re-upload.")

        if len(reader.pages) == 0:
            raise PDFProcessingError("The PDF document does not contain any pages.")

        if len(reader.pages) > self.max_pages:
            raise PDFProcessingError(
                f"Document exceeds maximum supported page count of {self.max_pages} pages (has {len(reader.pages)})."
            )

    def extract_text(self, file_bytes: bytes) -> List[Dict[str, Any]]:
        """
        Extracts text page by page from valid PDF bytes.
        Returns a list of dictionaries with page numbers (1-indexed) and clean extracted text.
        Raises an error if the document contains no extractable text (e.g. scanned images).
        """
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        pages_data = []
        total_text_length = 0

        for i, page in enumerate(reader.pages):
            page_num = i + 1
            try:
                page_text = page.extract_text() or ""
            except Exception as e:
                # If a single page has a font decoding issue, log and continue with partial text
                page_text = ""
            
            # Normalize whitespace while preserving paragraphs
            normalized = self._normalize_text(page_text)
            char_count = len(normalized)
            total_text_length += char_count

            pages_data.append({
                "page_number": page_num,
                "text": normalized,
                "character_count": char_count
            })

        # Check if entire PDF contains no extractable text (Scanned document detection)
        if total_text_length < 20:
            raise PDFProcessingError(
                "This PDF contains no extractable text (scanned document or image-only pages). "
                "Text-based search requires OCR, which is not currently implemented."
            )

        return pages_data

    def _normalize_text(self, text: str) -> str:
        if not text:
            return ""
        # Remove null bytes and control chars except newlines/tabs
        cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
        # Normalize multiple horizontal spaces
        cleaned = re.sub(r'[ \t]+', ' ', cleaned)
        # Normalize multiple line breaks to maximum two
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
        return cleaned.strip()

    def save_file(self, doc_id: str, file_bytes: bytes) -> str:
        """
        Saves document safely using uuid-derived filename to prevent path traversal.
        """
        safe_name = f"{doc_id}.pdf"
        target_path = self.upload_dir / safe_name
        with open(target_path, "wb") as f:
            f.write(file_bytes)
        return str(target_path)

    def delete_file(self, file_path: str) -> bool:
        """
        Safely deletes a stored document file if it exists.
        """
        try:
            p = Path(file_path)
            if p.exists() and p.is_file():
                p.unlink()
                return True
        except Exception:
            pass
        return False


pdf_service = PDFService()
