"""Text chunking service with configurable size and overlap."""
import re
from typing import List, Optional, Tuple
from dataclasses import dataclass

from app.core.config import settings


@dataclass
class TextChunk:
    chunk_index: int
    text: str
    page_number: Optional[int] = None


class ChunkingService:
    def __init__(
        self,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
    ):
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap
        if self.chunk_overlap >= self.chunk_size:
            self.chunk_overlap = max(0, self.chunk_size // 4)

    def chunk_extracted_pages(
        self, pages: List[Tuple[str, Optional[int]]]
    ) -> List[TextChunk]:
        """
        Chunks text while preserving page number boundaries where possible.
        """
        chunks: List[TextChunk] = []
        global_index = 0

        for page_text, page_number in pages:
            page_chunks = self._chunk_single_text(page_text, page_number, start_index=global_index)
            chunks.extend(page_chunks)
            global_index += len(page_chunks)

        return chunks

    def _chunk_single_text(
        self, text: str, page_number: Optional[int], start_index: int = 0
    ) -> List[TextChunk]:
        clean_text = text.strip()
        if not clean_text:
            return []

        # If text is already smaller than or equal to chunk_size, return 1 chunk
        if len(clean_text) <= self.chunk_size:
            return [TextChunk(chunk_index=start_index, text=clean_text, page_number=page_number)]

        chunks: List[TextChunk] = []
        current_pos = 0
        text_length = len(clean_text)
        current_index = start_index

        while current_pos < text_length:
            target_end = min(current_pos + self.chunk_size, text_length)

            # If we haven't reached the end, try to find a natural break point (paragraph or sentence)
            if target_end < text_length:
                break_point = self._find_break_point(clean_text, current_pos, target_end)
                end_pos = break_point if break_point > current_pos + (self.chunk_size // 2) else target_end
            else:
                end_pos = target_end

            chunk_content = clean_text[current_pos:end_pos].strip()
            if chunk_content:
                chunks.append(
                    TextChunk(
                        chunk_index=current_index,
                        text=chunk_content,
                        page_number=page_number,
                    )
                )
                current_index += 1

            if end_pos >= text_length:
                break

            # Advance by step size (chunk_size - overlap)
            next_start = end_pos - self.chunk_overlap
            current_pos = max(next_start, current_pos + 1)

        return chunks

    def _find_break_point(self, text: str, start: int, end: int) -> int:
        """Finds the best sentence or paragraph boundary before `end`."""
        segment = text[start:end]

        # 1. Paragraph boundary: '\n\n'
        para_idx = segment.rfind("\n\n")
        if para_idx != -1:
            return start + para_idx + 2

        # 2. Line boundary: '\n'
        newline_idx = segment.rfind("\n")
        if newline_idx != -1:
            return start + newline_idx + 1

        # 3. Sentence boundary: '. ', '! ', '? '
        sentence_end = max(
            segment.rfind(". "),
            segment.rfind("! "),
            segment.rfind("? "),
        )
        if sentence_end != -1:
            return start + sentence_end + 2

        # 4. Word boundary: ' '
        space_idx = segment.rfind(" ")
        if space_idx != -1:
            return start + space_idx + 1

        return end
