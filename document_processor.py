"""Document processor - PDF, Word, OCR support (OCR optional for cloud)"""
import os
import uuid
from pathlib import Path
from typing import List, Dict
import pdfplumber
import fitz  # PyMuPDF
from docx import Document
from PIL import Image
import io

class DocumentChunk:
    """Document chunk with text content and source information"""
    def __init__(self, text: str, source: str, page: int = None, chunk_id: str = None):
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
    """Document processor supporting multiple file formats"""
    
    def __init__(self):
        self.ocr_engine = None
        self.ocr_available = False
        # Try to load OCR (may fail on cloud)
        self._try_load_ocr()
    
    def _try_load_ocr(self):
        """Try to load OCR - cloud environments usually fail, but main features still work"""
        try:
            from paddleocr import PaddleOCR
            self.ocr_engine = PaddleOCR(lang='en')
            self.ocr_available = True
        except Exception:
            try:
                self.ocr_engine = PaddleOCR(use_angle_cls=True, lang='en')
                self.ocr_available = True
            except Exception:
                self.ocr_available = False
                self.ocr_engine = None
    
    def process_pdf(self, file_path: str) -> List[DocumentChunk]:
        """Process PDF file - extract text from all pages"""
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
                
                # OCR for images (only if OCR is available)
                if self.ocr_engine and self.ocr_available:
                    try:
                        image_list = page.get_images(full=True)
                        for img_index, img in enumerate(image_list):
                            xref = img[0]
                            base_image = doc.extract_image(xref)
                            image_bytes = base_image["image"]
                            
                            image = Image.open(io.BytesIO(image_bytes))
                            import numpy as np
                            img_array = np.array(image)
                            
                            try:
                                ocr_result = self.ocr_engine.predict(img_array)
                            except AttributeError:
                                ocr_result = self.ocr_engine.ocr(img_array, cls=True)
                            
                            if ocr_result:
                                ocr_text = ""
                                if isinstance(ocr_result, list) and len(ocr_result) > 0:
                                    result_data = ocr_result[0] if isinstance(ocr_result[0], list) else ocr_result
                                    if result_data and len(result_data) > 0:
                                        ocr_text = "\n".join([
                                            line[1][0] if isinstance(line[1], tuple) else str(line[1])
                                            for line in result_data
                                        ])
                                elif isinstance(ocr_result, dict):
                                    if 'rec_text' in ocr_result:
                                        ocr_text = "\n".join(ocr_result['rec_text'])
                                
                                if ocr_text.strip():
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
        """Process Word document"""
        chunks = []
        filename = os.path.basename(file_path)
        
        try:
            doc = Document(file_path)
            
            for para_num, paragraph in enumerate(doc.paragraphs):
                text = paragraph.text.strip()
                if text:
                    chunks.append(DocumentChunk(
                        text=text,
                        source=filename,
                        page=para_num + 1
                    ))
            
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
        """Auto-detect file type and process"""
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
