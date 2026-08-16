"""Document processor - PDF, Word, OCR support via Tesseract"""
import os
import uuid
from pathlib import Path
from typing import List, Dict
import pdfplumber
import fitz  # PyMuPDF
from docx import Document
from PIL import Image
import io
import numpy as np


class DocumentChunk:
    """Document chunk with text content and source information"""

    def __init__(self, text: str, source: str, page=None, chunk_id: str = None):
        self.text = text
        self.source = source
        self.page = page
        self.chunk_id = chunk_id or str(uuid.uuid4())

    def to_dict(self) -> Dict:
        return {
            'text': self.text,
            'source': self.source,
            'page': self.page,
            'chunk_id': self.chunk_id
        }


class DocumentProcessor:
    """Document processor supporting multiple file formats + OCR via Tesseract"""

    def __init__(self):
        self.ocr_available = False
        self._try_load_ocr()

    def _try_load_ocr(self):
        """Try to load Tesseract OCR."""
        try:
            import pytesseract
            # Check if tesseract is installed
            pytesseract.get_tesseract_version()
            self.ocr_engine = pytesseract
            self.ocr_available = True
        except Exception:
            self.ocr_available = False
            self.ocr_engine = None

    def _ocr_image(self, image: Image.Image) -> str:
        """Extract text from a PIL Image using Tesseract."""
        if not self.ocr_available or self.ocr_engine is None:
            return ""
        try:
            # Optional preprocessing: convert to grayscale, threshold, etc.
            # For now, we just pass the image directly
            text = self.ocr_engine.image_to_string(image, lang='eng')
            return text.strip()
        except Exception:
            return ""

    def process_pdf(self, file_path: str) -> List[DocumentChunk]:
        """Process PDF file - extract text from all pages, with OCR for images."""
        chunks = []
        filename = os.path.basename(file_path)

        try:
            doc = fitz.open(file_path)

            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()

                if text.strip():
                    chunks.append(DocumentChunk(
                        text=text,
                        source=filename,
                        page=page_num + 1
                    ))

                # OCR for embedded images (only if OCR is available)
                if self.ocr_available:
                    try:
                        image_list = page.get_images(full=True)
                        for img_index, img in enumerate(image_list):
                            xref = img[0]
                            base_image = doc.extract_image(xref)
                            image_bytes = base_image["image"]

                            image = Image.open(io.BytesIO(image_bytes))
                            ocr_text = self._ocr_image(image)
                            if ocr_text:
                                chunks.append(DocumentChunk(
                                    text=f"[OCR image text] {ocr_text}",
                                    source=filename,
                                    page=page_num + 1
                                ))
                    except Exception as e:
                        print(f"OCR failed (page {page_num + 1}): {e}")

            doc.close()
        except Exception as e:
            print(f"PyMuPDF processing failed: {e}")
            # Fallback to pdfplumber
            try:
                with pdfplumber.open(file_path) as pdf:
                    for page_num, page in enumerate(pdf.pages):
                        text = page.extract_text()
                        if text:
                            chunks.append(DocumentChunk(
                                text=text,
                                source=filename,
                                page=page_num + 1
                            ))
            except Exception as e2:
                print(f"pdfplumber also failed: {e2}")

        return chunks

    def process_word(self, file_path: str) -> List[DocumentChunk]:
        """Process Word document (paragraphs and tables)."""
        chunks = []
        filename = os.path.basename(file_path)

        try:
            doc = Document(file_path)

            # Paragraphs
            for para_num, paragraph in enumerate(doc.paragraphs):
                text = paragraph.text.strip()
                if text:
                    chunks.append(DocumentChunk(
                        text=text,
                        source=filename,
                        page=para_num + 1
                    ))

            # Tables
            for table_num, table in enumerate(doc.tables):
                for row in table.rows:
                    row_text = " | ".join([cell.text.strip() for cell in row.cells])
                    if row_text.strip():
                        chunks.append(DocumentChunk(
                            text=row_text,
                            source=filename,
                            page=f"Table {table_num + 1}"
                        ))
        except Exception as e:
            print(f"Word processing failed: {e}")

        return chunks

    def process_file(self, file_path: str) -> List[DocumentChunk]:
        """Auto-detect file type and process."""
        ext = Path(file_path).suffix.lower()

        if ext == '.pdf':
            return self.process_pdf(file_path)
        elif ext in ['.docx', '.doc']:
            return self.process_word(file_path)
        else:
            print(f"Unsupported file format: {ext}")
            return []


if __name__ == "__main__":
    processor = DocumentProcessor()
    print(f"OCR available: {processor.ocr_available}")
