import fitz  # PyMuPDF
from pdfminer.high_level import extract_text as pdfminer_extract_text
import pytesseract
from typing import List, Tuple
from PIL import Image
import io
import re
from src.app.utils.config import settings
from src.app.utils.exceptions import OCRError, FileProcessingError


class MarkdownOCRService:
    """OCR service for converting PDFs to markdown format"""
    
    def __init__(self):
        # Configure Tesseract if path is provided
        if settings.TESSERACT_CMD:
            pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD
    
    async def convert_pdf_to_markdown(self, file_path: str) -> List[Tuple[int, str]]:
        """
        Convert PDF to markdown format page by page
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            List of tuples: (page_number, markdown_content)
        """
        try:
            doc = fitz.open(file_path)
            page_results = []
            
            for page_num in range(doc.page_count):
                page = doc[page_num]
                
                # Extract text from this page
                page_text = page.get_text()
                
                # If no text found, try OCR on this page
                if not page_text.strip():
                    page_text = await self._ocr_page(page)
                
                # Convert text to markdown format
                markdown_content = await self._text_to_markdown(page_text.strip())
                
                # Store results: (page_number, markdown_content)
                page_results.append((page_num + 1, markdown_content))
            
            doc.close()
            return page_results
        except Exception as e:
            raise OCRError(f"PDF to markdown conversion failed: {str(e)}")
    
    async def _ocr_page(self, page) -> str:
        """Perform OCR on a single page"""
        try:
            # Convert page to image for OCR with higher resolution
            mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for better OCR
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            
            # Try OCR with multiple configurations
            try:
                # First try with default settings
                text = pytesseract.image_to_string(img, lang='eng')
                if text.strip():
                    return text
                
                # If no text, try with different PSM (Page Segmentation Mode)
                text = pytesseract.image_to_string(img, lang='eng', config='--psm 6')
                if text.strip():
                    return text
                    
                # Try with OCR Engine Mode 1 (Neural nets LSTM only)
                text = pytesseract.image_to_string(img, lang='eng', config='--oem 1 --psm 6')
                return text  # Return even if empty
                
            except Exception as ocr_error:
                print(f"OCR processing warning: {str(ocr_error)}")
                return ""  # Return empty string instead of raising error
                
        except Exception as e:
            print(f"OCR page conversion failed: {str(e)}")
            return ""  # Return empty string instead of raising error
    
    async def _text_to_markdown(self, text: str) -> str:
        """
        Convert extracted text to markdown format
        
        This method attempts to structure the text in a meaningful way:
        - Identifies titles and headers
        - Preserves mathematical expressions
        - Formats lists and numbered items
        - Maintains paragraph structure
        """
        if not text.strip():
            return "*(Empty page)*"
        
        lines = text.split('\n')
        markdown_lines = []
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                markdown_lines.append('')
                continue
            
            # Detect headers (lines that are short and followed by content)
            if len(line) < 100 and i < len(lines) - 1 and lines[i + 1].strip():
                # Check if this could be a title/header
                if (line.isupper() or 
                    any(word in line.lower() for word in ['question', 'problem', 'exercise', 'part', 'section']) or
                    re.match(r'^[A-Z][^.]*[^.]$', line)):
                    markdown_lines.append(f"## {line}")
                    continue
            
            # Detect numbered questions or parts
            if re.match(r'^\d+[\.)]\s*', line):
                markdown_lines.append(f"### {line}")
                continue
            
            # Detect lettered parts (a), b), etc.
            if re.match(r'^[a-z][\.)]\s*', line):
                markdown_lines.append(f"**{line}**")
                continue
            
            # Detect mathematical expressions and formulas
            if self._contains_math(line):
                # Wrap potential math content in code blocks for preservation
                markdown_lines.append(f"`{line}`")
                continue
            
            # Detect lists or bullet points
            if re.match(r'^[-•*]\s*', line) or re.match(r'^\(\w+\)\s*', line):
                markdown_lines.append(f"- {line}")
                continue
            
            # Regular paragraph text
            markdown_lines.append(line)
        
        # Join lines and clean up extra whitespace
        markdown_content = '\n'.join(markdown_lines)
        
        # Clean up multiple consecutive newlines
        markdown_content = re.sub(r'\n{3,}', '\n\n', markdown_content)
        
        return markdown_content.strip()
    
    def _contains_math(self, text: str) -> bool:
        """
        Check if text contains mathematical expressions
        """
        math_indicators = [
            r'[=<>≤≥≠±∓×÷∏∑∫∂∇]',  # Mathematical operators
            r'\d+/\d+',                # Fractions
            r'[a-zA-Z]+\^[a-zA-Z0-9]+',  # Powers
            r'√[a-zA-Z0-9]+',          # Square roots
            r'(sin|cos|tan|log|ln|exp|sqrt)\(',  # Functions
            r'\$[^$]+\$',              # LaTeX math
            r'[a-zA-Z]\s*[=]\s*[0-9a-zA-Z\s\+\-\*/\^\(\)]+',  # Equations
        ]
        
        for pattern in math_indicators:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False
    
    async def convert_single_pdf_to_markdown(self, file_path: str) -> str:
        """
        Convert entire PDF to a single markdown document
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Single markdown string with all pages
        """
        try:
            page_results = await self.convert_pdf_to_markdown(file_path)
            
            if not page_results:
                return "*(No content found)*"
            
            # Combine all pages into one markdown document
            markdown_parts = []
            
            for page_num, markdown_content in page_results:
                if len(page_results) > 1:  # Only add page headers if multiple pages
                    markdown_parts.append(f"# Page {page_num}")
                    markdown_parts.append("")
                
                markdown_parts.append(markdown_content)
                
                if page_num < len(page_results):  # Add separator between pages
                    markdown_parts.append("")
                    markdown_parts.append("---")
                    markdown_parts.append("")
            
            return '\n'.join(markdown_parts)
        except Exception as e:
            raise OCRError(f"Single PDF to markdown conversion failed: {str(e)}")


# Global markdown OCR service instance
markdown_ocr_service = MarkdownOCRService()