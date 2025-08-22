import uuid
import hashlib
import aiohttp
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime


def generate_id() -> str:
    """Generate a unique ID."""
    return str(uuid.uuid4())


def generate_chunk_id(content: str, source_file: str, chunk_index: int) -> str:
    """Generate a deterministic chunk ID based on content and metadata."""
    combined = f"{content}{source_file}{chunk_index}"
    return hashlib.md5(combined.encode()).hexdigest()


def setup_logging(service_name: str) -> logging.Logger:
    """Setup logging for a service."""
    logging.basicConfig(
        level=logging.INFO,
        format=f"%(asctime)s - {service_name} - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(f"{service_name}.log")
        ]
    )
    return logging.getLogger(service_name)


async def make_http_request(
    url: str,
    method: str = "GET",
    json_data: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """Make an HTTP request to another service."""
    async with aiohttp.ClientSession() as session:
        async with session.request(
            method=method,
            url=url,
            json=json_data,
            headers=headers
        ) as response:
            response.raise_for_status()
            return await response.json()


def validate_file_type(filename: str, allowed_types: List[str]) -> bool:
    """Validate if file type is allowed."""
    file_extension = filename.lower().split('.')[-1]
    return file_extension in allowed_types


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """Split text into overlapping chunks."""
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # Try to break at word boundary
        if end < len(text):
            while end > start and text[end] not in [' ', '\n', '\t', '.', '!', '?']:
                end -= 1
            if end == start:  # No word boundary found
                end = start + chunk_size
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        start = end - overlap
        if start >= len(text):
            break
    
    return chunks


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage."""
    import re
    # Remove or replace unsafe characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:255-len(ext)-1] + '.' + ext if ext else name[:255]
    return filename


def calculate_similarity(text1: str, text2: str) -> float:
    """Calculate simple text similarity (placeholder for more sophisticated methods)."""
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    
    if not words1 and not words2:
        return 1.0
    if not words1 or not words2:
        return 0.0
    
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    return len(intersection) / len(union)