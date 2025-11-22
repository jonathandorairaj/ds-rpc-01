"""
File parsing service for handling various file formats.

Supports:
- Markdown (.md)
- CSV (.csv)
- PDF (.pdf)
"""

import pdfplumber
import pandas as pd
from pathlib import Path
from typing import Tuple, Optional


class FileParser:
    """Parse different file formats into text content."""
    
    SUPPORTED_FORMATS = {".md", ".csv", ".pdf"}
    
    @staticmethod
    def parse_file(file_content: bytes, filename: str) -> Tuple[str, str]:
        """
        Parse uploaded file and return (content, format).
        
        Args:
            file_content: Raw file bytes
            filename: Original filename (used to detect format)
            
        Returns:
            (content: str, file_format: str)
            
        Raises:
            ValueError: If file format not supported
        """
        file_ext = Path(filename).suffix.lower()
        
        if file_ext == ".md":
            return FileParser._parse_markdown(file_content), "markdown"
        elif file_ext == ".csv":
            return FileParser._parse_csv(file_content), "csv"
        elif file_ext == ".pdf":
            return FileParser._parse_pdf(file_content), "pdf"
        else:
            raise ValueError(
                f"Unsupported file format: {file_ext}. "
                f"Supported: {', '.join(FileParser.SUPPORTED_FORMATS)}"
            )
    
    @staticmethod
    def _parse_markdown(file_content: bytes) -> str:
        """Parse markdown file."""
        return file_content.decode("utf-8")
    
    @staticmethod
    def _parse_csv(file_content: bytes) -> str:
        """Parse CSV file and convert to readable text."""
        try:
            df = pd.read_csv(__import__('io').BytesIO(file_content))
            return df.to_string()
        except Exception as e:
            raise ValueError(f"Failed to parse CSV: {str(e)}")
    
    @staticmethod
    def _parse_pdf(file_content: bytes) -> str:
        """Extract text from PDF."""
        try:
            text = ""
            with pdfplumber.open(__import__('io').BytesIO(file_content)) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    page_text = page.extract_text()
                    if page_text:
                        text += f"\n--- Page {page_num} ---\n{page_text}"
            
            if not text.strip():
                raise ValueError("No text extracted from PDF")
            
            return text
        except Exception as e:
            raise ValueError(f"Failed to parse PDF: {str(e)}")
    
    @staticmethod
    def validate_filename(filename: str) -> bool:
        """Check if filename has supported extension."""
        return Path(filename).suffix.lower() in FileParser.SUPPORTED_FORMATS
    
    @staticmethod
    def get_department_from_filename(filename: str) -> Optional[str]:
        """
        Try to infer department from filename.
        
        Examples:
            "finance_report.pdf" → "finance"
            "q4_marketing.csv" → "marketing"
        
        Returns None if can't infer.
        """
        name_lower = filename.lower()
        
        departments = {
            "finance": ["finance", "financial", "quarterly", "revenue", "expense"],
            "marketing": ["marketing", "campaign", "sales", "customer"],
            "hr": ["hr", "employee", "payroll", "attendance"],
            "engineering": ["engineering", "technical", "architecture", "development"],
        }
        
        for dept, keywords in departments.items():
            if any(keyword in name_lower for keyword in keywords):
                return dept
        
        return None
