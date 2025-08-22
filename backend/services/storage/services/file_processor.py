import json
import aiofiles
from typing import List
import PyPDF2
from docx import Document
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from shared.models import DocumentChunk, FileType
from shared.config import settings
from shared.utils import chunk_text, generate_chunk_id


class FileProcessor:
    """Service for processing different file types."""
    
    async def extract_text(self, file_path: str, file_type: FileType) -> str:
        """Extract text content from uploaded file."""
        try:
            if file_type == FileType.PDF:
                return await self._extract_pdf_text(file_path)
            elif file_type == FileType.DOCX:
                return await self._extract_docx_text(file_path)
            elif file_type == FileType.TXT:
                return await self._extract_txt_text(file_path)
            elif file_type == FileType.JSON:
                return await self._extract_json_text(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
        except Exception as e:
            raise Exception(f"Error extracting text from {file_type} file: {e}")
    
    async def _extract_pdf_text(self, file_path: str) -> str:
        """Extract text from PDF file."""
        text = ""
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text.strip()
    
    async def _extract_docx_text(self, file_path: str) -> str:
        """Extract text from DOCX file."""
        doc = Document(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text.strip()
    
    async def _extract_txt_text(self, file_path: str) -> str:
        """Extract text from TXT file."""
        async with aiofiles.open(file_path, mode='r', encoding='utf-8') as file:
            content = await file.read()
        return content.strip()
    
    async def _extract_json_text(self, file_path: str) -> str:
        """Extract text from JSON file."""
        async with aiofiles.open(file_path, mode='r', encoding='utf-8') as file:
            content = await file.read()
            data = json.loads(content)
        
        # Convert JSON to readable text
        return self._json_to_text(data)
    
    def _json_to_text(self, data, prefix="") -> str:
        """Convert JSON data to readable text."""
        text_parts = []
        
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    text_parts.append(f"{prefix}{key}:")
                    text_parts.append(self._json_to_text(value, prefix + "  "))
                else:
                    text_parts.append(f"{prefix}{key}: {value}")
        elif isinstance(data, list):
            for i, item in enumerate(data):
                text_parts.append(f"{prefix}[{i}]: {self._json_to_text(item, prefix + '  ')}")
        else:
            text_parts.append(str(data))
        
        return "\n".join(text_parts)
    
    async def chunk_text(self, text: str, source_file: str = "") -> List[DocumentChunk]:
        """Split text into chunks and create DocumentChunk objects."""
        text_chunks = chunk_text(
            text, 
            chunk_size=settings.chunk_size, 
            overlap=settings.chunk_overlap
        )
        
        document_chunks = []
        for i, chunk_content in enumerate(text_chunks):
            chunk_id = generate_chunk_id(chunk_content, source_file, i)
            
            chunk = DocumentChunk(
                id=chunk_id,
                content=chunk_content,
                metadata={
                    "source_file": source_file,
                    "chunk_index": i,
                    "total_chunks": len(text_chunks),
                    "char_count": len(chunk_content)
                },
                source_file=source_file,
                chunk_index=i
            )
            document_chunks.append(chunk)
        
        return document_chunks