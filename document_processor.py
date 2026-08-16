"""Document processor - PDF, Word, OCR support with Tesseract or EasyOCR fallback"""
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
    """Document processor with OCR support (Tesseract first, EasyOCR fallback)"""

    def __init__(self):
        self.ocr_available = False
        self.ocr_engine = None
        self._try_load_ocr()

    def _try_load_ocr(self):
        """Try Tesseract, fallback to EasyOCR if it fails."""
        # 1. Try Tesseract
        try:
            import pytesseract
            # Check if tesseract binary is available
            pytesseract.get_tesseract_version()
            self.ocr_engine = pytesseract
            self.ocr_available = True
            print("✅ Tesseract OCR loaded.")
            return
        except Exception as e:
            print(f"⚠️ Tesseract not available: {e}")

        # 2. Fallback to EasyOCR
        try:
            import easyocr
            # Use CPU only (no GPU required)
            self.ocr_engine = easyocr.Reader(['en'], gpu=False)
            self.ocr_available = True
            print("✅ EasyOCR loaded (fallback).")
        except Exception as e:
            print(f"❌ EasyOCR also failed: {e}")
            self.ocr_available = False
            self.ocr_engine = None

    def _ocr_image(self, image: Image.Image) -> str:
        """Extract text from a PIL Image using the available OCR engine."""
        if not self.ocr_available or self.ocr_engine is None:
            return ""

        try:
            # Tesseract
            if hasattr(self.ocr_engine, 'image_to_string'):
                text = self.ocr_engine.image_to_string(image, lang='eng')
                return text.strip()
            # EasyOCR
            else:
                import numpy as np
                img_array = np.array(image)
                result = self.ocr_engine.readtext(img_array)
                text = "\n".join([item[1] for item in result])
                return text.strip()
        except Exception as e:
            print(f"OCR error on image: {e}")
            return ""

    def process_pdf(self, file_path: str) -> List[DocumentChunk]:
        """Process PDF file - extract text and OCR images."""
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

                # OCR for embedded images (if OCR is available)
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
                        print(f"OCR failed on page {page_num + 1}: {e}")

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
