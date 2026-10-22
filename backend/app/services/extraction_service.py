"""Text extraction service for PDF, TXT, Markdown, and notes."""
from pathlib import Path
from typing import List, Optional, Tuple
import fitz  # PyMuPDF

from app.core.logging import logger
from app.db.models.document import FileType


class ExtractionError(Exception):
    """Raised when document extraction fails."""
    pass


class ExtractionService:
    @staticmethod
    def extract_from_file(file_path: Path, file_type: FileType) -> List[Tuple[str, Optional[int]]]:
        """
        Extracts text from a saved file.
        Returns a list of tuples: (extracted_text_content, optional_page_number).
        """
        if not file_path.exists():
            raise ExtractionError(f"File not found: {file_path}")

        try:
            if file_type == FileType.PDF:
                return ExtractionService._extract_pdf(file_path)
            elif file_type == FileType.TXT:
                return ExtractionService._extract_plain_text(file_path)
            elif file_type == FileType.MARKDOWN:
                return ExtractionService._extract_markdown(file_path)
            elif file_type == FileType.NOTE:
                return ExtractionService._extract_plain_text(file_path)
            else:
                raise ExtractionError(f"Unsupported file type: {file_type}")
        except ExtractionError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error extracting {file_path}: {e}", exc_info=True)
            raise ExtractionError(f"Failed to extract document contents: {str(e)}")

    @staticmethod
    def extract_from_text(text: str) -> List[Tuple[str, Optional[int]]]:
        """Extracts text from direct note content."""
        clean = text.strip()
        if not clean:
            raise ExtractionError("Note content is empty.")
        return [(clean, None)]

    @staticmethod
    def _extract_pdf(file_path: Path) -> List[Tuple[str, Optional[int]]]:
        results: List[Tuple[str, Optional[int]]] = []
        try:
            doc = fitz.open(str(file_path))
            total_pages = len(doc)
            if total_pages == 0:
                raise ExtractionError("PDF document has 0 pages.")

            total_characters = 0
            for page_index in range(total_pages):
                page = doc[page_index]
                page_text = page.get_text("text").strip()
                page_num = page_index + 1
                if page_text:
                    total_characters += len(page_text)
                    results.append((page_text, page_num))

            doc.close()

            # Scanned PDF detection: if all pages contain 0 extractable text characters
            if total_characters == 0 or len(results) == 0:
                raise ExtractionError(
                    "This PDF contains only scanned images or unextractable text. "
                    "OCR is not enabled in this environment. Please upload a PDF with embedded text or a TXT/Markdown file."
                )

            return results
        except fitz.FileDataError as e:
            raise ExtractionError(f"Corrupt or unreadable PDF file: {str(e)}")
        except Exception as e:
            if isinstance(e, ExtractionError):
                raise
            raise ExtractionError(f"PDF extraction error: {str(e)}")

    @staticmethod
    def _extract_plain_text(file_path: Path) -> List[Tuple[str, Optional[int]]]:
        encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
        content = None
        for enc in encodings:
            try:
                with open(file_path, "r", encoding=enc) as f:
                    content = f.read()
                break
            except UnicodeDecodeError:
                continue

        if content is None:
            raise ExtractionError("Could not decode text file with standard UTF-8 or Latin-1 encodings.")

        clean = content.strip()
        if not clean:
            raise ExtractionError("File contains no readable text content.")
        return [(clean, None)]

    @staticmethod
    def _extract_markdown(file_path: Path) -> List[Tuple[str, Optional[int]]]:
        # Plain text extraction with preservation of markdown structure
        return ExtractionService._extract_plain_text(file_path)
