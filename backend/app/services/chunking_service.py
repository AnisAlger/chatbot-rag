import math
import re
from typing import Any, Dict, List
from app.config import settings


class ChunkingService:
    """
    Splits extracted PDF page text into semantically cohesive chunks while preserving
    strict document ownership, page references, and metadata.
    
    Chunking Assumptions & Characteristics:
    - 1 token ≈ 4 characters for English / European languages.
    - Default chunk_size of 800 tokens corresponds to approximately 3,200 characters.
    - Default chunk_overlap of 100 tokens corresponds to approximately 400 characters.
    - Paragraph and sentence boundaries are preferred to avoid cutting words or statements mid-sentence.
    """

    def __init__(self, chunk_size_tokens: int = settings.CHUNK_SIZE, overlap_tokens: int = settings.CHUNK_OVERLAP):
        self.chunk_size_chars = chunk_size_tokens * 4
        self.overlap_chars = overlap_tokens * 4

    def chunk_document(
        self,
        document_id: str,
        owner_id: str,
        filename: str,
        pages_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Chunks the extracted text page by page.
        Produces structured chunks with full metadata, page numbers, and unique chunk IDs.
        """
        chunks: List[Dict[str, Any]] = []
        global_chunk_idx = 0

        for page_info in pages_data:
            page_num = page_info["page_number"]
            page_text = page_info["text"]

            if not page_text or len(page_text.strip()) == 0:
                continue

            page_chunks = self._split_text(page_text)

            for text_chunk in page_chunks:
                if not text_chunk.strip():
                    continue

                chunk_id = f"{document_id}_c{global_chunk_idx}"
                chunks.append({
                    "chunk_id": chunk_id,
                    "document_id": document_id,
                    "owner_id": owner_id,
                    "filename": filename,
                    "page_number": page_num,
                    "chunk_index": global_chunk_idx,
                    "text": text_chunk,
                    "character_count": len(text_chunk),
                    "token_estimate": max(1, math.ceil(len(text_chunk) / 4))
                })
                global_chunk_idx += 1

        return chunks

    def _split_text(self, text: str) -> List[str]:
        """
        Recursively splits text using paragraph breaks, sentence stops, or length boundaries.
        """
        text = text.strip()
        if len(text) <= self.chunk_size_chars:
            return [text]

        # Paragraph split
        paragraphs = re.split(r'\n\s*\n', text)
        result_chunks: List[str] = []
        current_chunk = ""

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # If single paragraph exceeds max chunk size, break by sentence
            if len(para) > self.chunk_size_chars:
                sentences = re.split(r'(?<=[.!?])\s+', para)
                for sentence in sentences:
                    sentence = sentence.strip()
                    if not sentence:
                        continue
                    if len(current_chunk) + len(sentence) + 1 <= self.chunk_size_chars:
                        current_chunk = f"{current_chunk} {sentence}".strip()
                    else:
                        if current_chunk:
                            result_chunks.append(current_chunk)
                            # Create overlap from end of current_chunk
                            current_chunk = self._get_overlap_suffix(current_chunk)
                        
                        # If a single sentence is still larger than chunk_size, hard slice it
                        while len(sentence) > self.chunk_size_chars:
                            result_chunks.append(sentence[:self.chunk_size_chars])
                            sentence = sentence[self.chunk_size_chars - self.overlap_chars:]
                        current_chunk = f"{current_chunk} {sentence}".strip()
            else:
                if len(current_chunk) + len(para) + 2 <= self.chunk_size_chars:
                    current_chunk = f"{current_chunk}\n\n{para}".strip() if current_chunk else para
                else:
                    if current_chunk:
                        result_chunks.append(current_chunk)
                        current_chunk = self._get_overlap_suffix(current_chunk)
                    current_chunk = f"{current_chunk}\n\n{para}".strip() if current_chunk else para

        if current_chunk and current_chunk.strip():
            result_chunks.append(current_chunk.strip())

        return result_chunks

    def _get_overlap_suffix(self, text: str) -> str:
        """
        Extracts the last self.overlap_chars characters, aligned to a word boundary.
        """
        if len(text) <= self.overlap_chars:
            return text
        suffix = text[-self.overlap_chars:]
        # Align to word boundary if possible
        first_space = suffix.find(' ')
        if first_space != -1 and first_space < len(suffix) // 2:
            suffix = suffix[first_space + 1:]
        return suffix.strip()


chunking_service = ChunkingService()
