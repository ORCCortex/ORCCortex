import pytesseract
import fitz  # PyMuPDF
from pdfminer.high_level import extract_text as pdfminer_extract_text
import re
from typing import List, Tuple, Optional
from PIL import Image
import io
from src.app.utils.config import settings
from src.app.utils.exceptions import OCRError, FileProcessingError


class OCRService:
    """OCR service for extracting text and math from PDFs"""
    
    def __init__(self):
        # Configure Tesseract if path is provided
        if settings.TESSERACT_CMD:
            pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD
    
    async def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF using multiple methods"""
        try:
            # Try PyMuPDF first (better for most PDFs)
            text = await self._extract_with_pymupdf(file_path)
            
            # If no text found, try pdfminer
            if not text.strip():
                text = await self._extract_with_pdfminer(file_path)
            
            # If still no text, try OCR on images
            if not text.strip():
                text = await self._extract_with_ocr(file_path)
            
            return text.strip()
        except Exception as e:
            raise OCRError(f"Text extraction failed: {str(e)}")
    
    async def _extract_with_pymupdf(self, file_path: str) -> str:
        """Extract text using PyMuPDF"""
        try:
            doc = fitz.open(file_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text
        except Exception as e:
            raise OCRError(f"PyMuPDF extraction failed: {str(e)}")
    
    async def _extract_with_pdfminer(self, file_path: str) -> str:
        """Extract text using pdfminer"""
        try:
            return pdfminer_extract_text(file_path)
        except Exception as e:
            raise OCRError(f"PDFMiner extraction failed: {str(e)}")
    
    async def _extract_with_ocr(self, file_path: str) -> str:
        """Extract text using OCR on PDF images"""
        try:
            doc = fitz.open(file_path)
            text = ""
            
            for page_num in range(doc.page_count):
                page = doc[page_num]
                # Convert page to image
                pix = page.get_pixmap()
                img_data = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_data))
                
                # Perform OCR
                page_text = pytesseract.image_to_string(img, lang='eng')
                text += page_text + "\n"
            
            doc.close()
            return text
        except Exception as e:
            raise OCRError(f"OCR extraction failed: {str(e)}")
    
    async def extract_math_expressions(self, text: str) -> List[str]:
        """Extract mathematical expressions from text"""
        try:
            math_patterns = [
                # LaTeX-style math expressions
                r'\$[^$]+\$',
                r'\$\$[^$]+\$\$',
                r'\\begin\{[^}]+\}.*?\\end\{[^}]+\}',
                
                # Common math expressions
                r'[a-zA-Z0-9\s]*[=<>≤≥≠±∓×÷∏∑∫∂∇][a-zA-Z0-9\s]*',
                
                # Equations with variables and numbers
                r'[a-zA-Z]\s*[=]\s*[0-9a-zA-Z\s\+\-\*/\^\(\)]+',
                
                # Fractions
                r'\d+/\d+',
                r'[a-zA-Z]+/[a-zA-Z]+',
                
                # Powers and roots
                r'[a-zA-Z0-9]+\^[a-zA-Z0-9]+',
                r'√[a-zA-Z0-9]+',
                
                # Functions
                r'(sin|cos|tan|log|ln|exp|sqrt)\([^)]+\)',
            ]
            
            expressions = []
            for pattern in math_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
                expressions.extend(matches)
            
            # Remove duplicates and clean up
            unique_expressions = list(set(expressions))
            cleaned_expressions = [expr.strip() for expr in unique_expressions if len(expr.strip()) > 2]
            
            return cleaned_expressions
        except Exception as e:
            raise OCRError(f"Math expression extraction failed: {str(e)}")
    
    async def process_pdf(self, file_path: str) -> Tuple[str, List[str]]:
        """Process PDF to extract both text and math expressions"""
        try:
            # Extract text
            text = await self.extract_text_from_pdf(file_path)
            
            # Extract math expressions
            math_expressions = await self.extract_math_expressions(text)
            
            return text, math_expressions
        except Exception as e:
            raise OCRError(f"PDF processing failed: {str(e)}")


# Global OCR service instance
ocr_service = OCRService()