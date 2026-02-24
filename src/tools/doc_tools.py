"""
Documentation tools for PDF analysis and text extraction.

This module provides RAG-lite document processing capabilities for analyzing
PDF reports. It extracts text, chunks documents for efficient querying,
and identifies key concepts and file references.
"""

import re
import os
from typing import Dict, List, Optional, Tuple
from pathlib import Path

try:
    from PyPDF2 import PdfReader
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False

try:
    from docling import DocumentConverter
    DOCLING_AVAILABLE = True
except ImportError:
    DOCLING_AVAILABLE = False


# Default chunk size for RAG-lite approach (characters)
DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 200


def ingest_pdf(pdf_path: str, chunk_size: int = DEFAULT_CHUNK_SIZE, 
               chunk_overlap: int = DEFAULT_CHUNK_OVERLAP) -> Dict:
    """
    Extract text from a PDF and chunk it for RAG-lite querying.
    
    This function uses PyPDF2 (or docling if available) to extract text from
    a PDF document and splits it into overlapping chunks for efficient
    semantic search and context retrieval.
    
    Args:
        pdf_path: Path to the PDF file to ingest
        chunk_size: Maximum size of each text chunk in characters (default: 1000)
        chunk_overlap: Number of characters to overlap between chunks (default: 200)
    
    Returns:
        Dict: A structured dictionary containing:
            - full_text: Complete extracted text from the PDF
            - chunks: List of chunk dictionaries with:
                - text: The chunk text content
                - chunk_id: Unique identifier for the chunk
                - page_number: Source page number (if available)
                - start_char: Character offset in full text
                - end_char: Character offset in full text
            - total_pages: Total number of pages in the PDF
            - total_chunks: Number of chunks created
            - metadata: PDF metadata (title, author, etc.)
    
    Raises:
        FileNotFoundError: If the PDF file does not exist
        ValueError: If the PDF path is invalid
        RuntimeError: If PDF extraction fails (corrupted file, encryption, etc.)
    
    Example:
        >>> result = ingest_pdf("report.pdf")
        >>> print(result["total_pages"])
        10
        >>> print(len(result["chunks"]))
        15
    
    Notes:
        - Prefers docling if available (better extraction quality)
        - Falls back to PyPDF2 if docling is not available
        - Handles encrypted and corrupted PDFs gracefully
        - Chunks preserve context with overlap for better retrieval
    """
    # Validate input
    if not pdf_path or not isinstance(pdf_path, str):
        raise ValueError(f"Invalid PDF path: {pdf_path}")
    
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    if not pdf_path.lower().endswith('.pdf'):
        raise ValueError(f"File is not a PDF: {pdf_path}")
    
    try:
        # Try docling first (better quality)
        if DOCLING_AVAILABLE:
            return _ingest_pdf_docling(pdf_path, chunk_size, chunk_overlap)
        elif PYPDF2_AVAILABLE:
            return _ingest_pdf_pypdf2(pdf_path, chunk_size, chunk_overlap)
        else:
            raise RuntimeError(
                "No PDF library available. Please install PyPDF2 or docling: "
                "uv add PyPDF2"
            )
    except Exception as e:
        # Provide helpful error messages for common issues
        error_msg = str(e).lower()
        if "encrypted" in error_msg or "password" in error_msg:
            raise RuntimeError(
                f"PDF is encrypted and cannot be read: {pdf_path}. "
                "Please provide an unencrypted PDF."
            )
        elif "corrupted" in error_msg or "invalid" in error_msg:
            raise RuntimeError(
                f"PDF appears to be corrupted or invalid: {pdf_path}. "
                "Please verify the file is a valid PDF."
            )
        else:
            raise RuntimeError(
                f"Failed to extract text from PDF: {pdf_path}. Error: {str(e)}"
            )


def _ingest_pdf_docling(pdf_path: str, chunk_size: int, chunk_overlap: int) -> Dict:
    """Internal function to extract PDF using docling."""
    try:
        converter = DocumentConverter()
        doc = converter.convert(pdf_path)
        
        # Extract full text
        full_text = doc.document.export_to_text()
        
        # Extract metadata
        metadata = {
            "title": getattr(doc.document, "title", None),
            "author": getattr(doc.document, "author", None),
            "subject": getattr(doc.document, "subject", None),
        }
        
        # Estimate page count (docling doesn't always provide this directly)
        # Use approximate based on text length
        estimated_pages = max(1, len(full_text) // 2000)  # Rough estimate
        
        # Chunk the text
        chunks = _chunk_text(full_text, chunk_size, chunk_overlap)
        
        return {
            "full_text": full_text,
            "chunks": chunks,
            "total_pages": estimated_pages,
            "total_chunks": len(chunks),
            "metadata": metadata,
            "extraction_method": "docling"
        }
    except Exception as e:
        # Fallback to PyPDF2 if docling fails
        if PYPDF2_AVAILABLE:
            return _ingest_pdf_pypdf2(pdf_path, chunk_size, chunk_overlap)
        else:
            raise


def _ingest_pdf_pypdf2(pdf_path: str, chunk_size: int, chunk_overlap: int) -> Dict:
    """Internal function to extract PDF using PyPDF2."""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PdfReader(file)
            
            # Extract text from all pages
            full_text = ""
            page_texts = []
            
            for page_num, page in enumerate(reader.pages, start=1):
                try:
                    page_text = page.extract_text()
                    page_texts.append((page_num, page_text))
                    full_text += page_text + "\n\n"
                except Exception as e:
                    # Skip corrupted pages but continue processing
                    print(f"Warning: Failed to extract text from page {page_num}: {e}")
                    continue
            
            # Extract metadata
            metadata = {}
            if reader.metadata:
                metadata = {
                    "title": reader.metadata.get("/Title", None),
                    "author": reader.metadata.get("/Author", None),
                    "subject": reader.metadata.get("/Subject", None),
                    "creator": reader.metadata.get("/Creator", None),
                }
            
            # Chunk the text with page information
            chunks = _chunk_text_with_pages(
                full_text, 
                page_texts, 
                chunk_size, 
                chunk_overlap
            )
            
            return {
                "full_text": full_text,
                "chunks": chunks,
                "total_pages": len(reader.pages),
                "total_chunks": len(chunks),
                "metadata": metadata,
                "extraction_method": "pypdf2"
            }
    
    except Exception as e:
        # Check for specific error types
        if "encrypted" in str(e).lower():
            raise RuntimeError(
                f"PDF is encrypted: {pdf_path}. Cannot extract text."
            )
        elif "corrupted" in str(e).lower() or "invalid" in str(e).lower():
            raise RuntimeError(
                f"PDF appears corrupted: {pdf_path}. Cannot read file."
            )
        else:
            raise RuntimeError(
                f"PyPDF2 extraction failed: {str(e)}"
            )


def _chunk_text(text: str, chunk_size: int, chunk_overlap: int) -> List[Dict]:
    """
    Split text into overlapping chunks.
    
    Args:
        text: The full text to chunk
        chunk_size: Maximum size of each chunk
        chunk_overlap: Number of characters to overlap
    
    Returns:
        List of chunk dictionaries
    """
    chunks = []
    start = 0
    chunk_id = 0
    
    while start < len(text):
        end = start + chunk_size
        chunk_text = text[start:end]
        
        # Try to break at sentence boundaries
        if end < len(text):
            # Look for sentence endings in the overlap region
            overlap_region = text[max(start, end - chunk_overlap):end]
            sentence_end = max(
                overlap_region.rfind('. '),
                overlap_region.rfind('.\n'),
                overlap_region.rfind('.\t'),
            )
            if sentence_end > 0:
                end = start + (end - chunk_overlap) + sentence_end + 1
                chunk_text = text[start:end]
        
        if chunk_text.strip():  # Only add non-empty chunks
            chunks.append({
                "text": chunk_text.strip(),
                "chunk_id": chunk_id,
                "page_number": None,  # Will be set if page info available
                "start_char": start,
                "end_char": end
            })
            chunk_id += 1
        
        # Move start position with overlap
        start = end - chunk_overlap if end < len(text) else end
    
    return chunks


def _chunk_text_with_pages(
    full_text: str, 
    page_texts: List[Tuple[int, str]], 
    chunk_size: int, 
    chunk_overlap: int
) -> List[Dict]:
    """
    Split text into chunks with page number information.
    
    Args:
        full_text: The full concatenated text
        page_texts: List of (page_number, page_text) tuples
        chunk_size: Maximum size of each chunk
        chunk_overlap: Number of characters to overlap
    
    Returns:
        List of chunk dictionaries with page numbers
    """
    chunks = _chunk_text(full_text, chunk_size, chunk_overlap)
    
    # Map chunks to page numbers
    char_to_page = {}
    current_char = 0
    
    for page_num, page_text in page_texts:
        for _ in range(len(page_text)):
            char_to_page[current_char] = page_num
            current_char += 1
        # Account for page separators
        current_char += 2  # "\n\n"
    
    # Assign page numbers to chunks
    for chunk in chunks:
        start_char = chunk["start_char"]
        # Find the page for the start of this chunk
        page_num = char_to_page.get(start_char, None)
        if page_num is None:
            # Find closest page
            closest_char = min(
                char_to_page.keys(),
                key=lambda x: abs(x - start_char)
            )
            page_num = char_to_page.get(closest_char, 1)
        chunk["page_number"] = page_num
    
    return chunks


def extract_keywords(
    text: str, 
    keywords: Optional[List[str]] = None
) -> List[Dict]:
    """
    Extract specific keywords from text with surrounding context.
    
    This function searches for keywords and determines if they are used
    substantively (with explanation) or just dropped as buzzwords.
    
    Args:
        text: The text to search
        keywords: List of keywords to search for. If None, uses default
                 keywords: "Dialectical Synthesis", "Fan-In", "Fan-Out", 
                 "Metacognition", "State Synchronization"
    
    Returns:
        List of dictionaries containing:
            - keyword: The keyword found
            - context: Surrounding text (typically 200 chars before/after)
            - position: Character position in text
            - is_substantive: Boolean indicating if keyword is used with explanation
            - explanation_quality: Score 0-1 indicating depth of explanation
    
    Example:
        >>> results = extract_keywords(text, ["Dialectical Synthesis"])
        >>> print(results[0]["is_substantive"])
        True
    
    Analysis Logic:
        - Substantive: Keyword appears with surrounding explanation (50+ chars)
        - Buzzword: Keyword appears alone or with minimal context
        - Quality score based on explanation length and detail
    """
    if keywords is None:
        keywords = [
            "Dialectical Synthesis",
            "Fan-In",
            "Fan-Out",
            "Metacognition",
            "State Synchronization"
        ]
    
    if not text or not isinstance(text, str):
        return []
    
    results = []
    context_window = 200  # Characters before/after keyword
    
    for keyword in keywords:
        # Case-insensitive search with word boundaries
        pattern = re.compile(
            re.escape(keyword),
            re.IGNORECASE
        )
        
        for match in pattern.finditer(text):
            start_pos = match.start()
            end_pos = match.end()
            
            # Extract context
            context_start = max(0, start_pos - context_window)
            context_end = min(len(text), end_pos + context_window)
            context = text[context_start:context_end]
            
            # Analyze if substantive
            # Check if there's substantial explanation around the keyword
            before_text = text[max(0, start_pos - 100):start_pos].strip()
            after_text = text[end_pos:min(len(text), end_pos + 100)].strip()
            
            # Determine if substantive
            is_substantive = _is_keyword_substantive(
                keyword, 
                before_text, 
                after_text,
                context
            )
            
            # Calculate explanation quality score
            explanation_quality = _calculate_explanation_quality(
                before_text,
                after_text,
                context
            )
            
            results.append({
                "keyword": keyword,
                "context": context,
                "position": start_pos,
                "is_substantive": is_substantive,
                "explanation_quality": explanation_quality,
                "before_context": before_text[-50:] if len(before_text) > 50 else before_text,
                "after_context": after_text[:50] if len(after_text) > 50 else after_text
            })
    
    return results


def _is_keyword_substantive(
    keyword: str, 
    before_text: str, 
    after_text: str,
    full_context: str
) -> bool:
    """
    Determine if a keyword is used substantively or as a buzzword.
    
    Substantive use means the keyword appears with explanation or context
    that demonstrates understanding, not just name-dropping.
    """
    # Check for explanation indicators
    explanation_indicators = [
        "implemented", "executed", "applied", "used", "via", "through",
        "by", "using", "with", "how", "why", "because", "explains",
        "demonstrates", "shows", "illustrates", "means", "refers to"
    ]
    
    # Check if explanation exists in context
    context_lower = full_context.lower()
    keyword_lower = keyword.lower()
    
    # Find keyword position in context
    keyword_pos = context_lower.find(keyword_lower)
    if keyword_pos == -1:
        return False
    
    # Check surrounding text for explanation
    before_context = context_lower[max(0, keyword_pos - 150):keyword_pos]
    after_context = context_lower[keyword_pos + len(keyword):keyword_pos + len(keyword) + 150]
    
    # Count explanation indicators
    indicator_count = sum(
        1 for indicator in explanation_indicators
        if indicator in before_context or indicator in after_context
    )
    
    # Check for substantial text (not just keyword drop)
    substantial_text = len(before_context.strip()) > 20 or len(after_context.strip()) > 20
    
    # Substantive if: has indicators OR substantial explanation text
    return indicator_count >= 2 or (substantial_text and indicator_count >= 1)


def _calculate_explanation_quality(
    before_text: str, 
    after_text: str,
    full_context: str
) -> float:
    """
    Calculate a quality score (0-1) for keyword explanation.
    
    Higher scores indicate deeper, more substantive explanations.
    """
    score = 0.0
    
    # Length factor (more text = better explanation)
    total_length = len(before_text) + len(after_text)
    if total_length > 100:
        score += 0.3
    elif total_length > 50:
        score += 0.15
    
    # Technical detail indicators
    technical_terms = [
        "architecture", "implementation", "design", "pattern", "system",
        "process", "mechanism", "approach", "method", "strategy"
    ]
    
    context_lower = full_context.lower()
    technical_count = sum(1 for term in technical_terms if term in context_lower)
    score += min(0.4, technical_count * 0.1)
    
    # Sentence structure (complete sentences = better)
    if '.' in before_text or '.' in after_text:
        score += 0.2
    
    # Examples or specifics
    example_indicators = ["for example", "such as", "like", "including", "e.g."]
    if any(indicator in context_lower for indicator in example_indicators):
        score += 0.1
    
    return min(1.0, score)


def extract_file_paths(text: str) -> List[str]:
    """
    Extract file paths mentioned in text using regex patterns.
    
    This function identifies file paths that are mentioned in the document
    (e.g., "src/tools/ast_parser.py") for cross-referencing with actual
    repository structure.
    
    Args:
        text: The text to search for file paths
    
    Returns:
        List of unique file paths found in the text
    
    Example:
        >>> paths = extract_file_paths("We implemented src/tools/parser.py")
        >>> print(paths)
        ['src/tools/parser.py']
    
    Pattern Matching:
        - Unix-style paths: src/file.py, ./file.py, ../file.py
        - Windows-style paths: src\\file.py (normalized to Unix)
        - Absolute paths: /path/to/file.py, C:\\path\\to\\file.py
        - File extensions: .py, .js, .ts, .json, .md, .txt, etc.
    """
    if not text or not isinstance(text, str):
        return []
    
    # Pattern for common file paths
    # Matches: path/to/file.ext or path\\to\\file.ext
    patterns = [
        # Unix-style relative paths
        r'(?:\.{0,2}/)?(?:[a-zA-Z0-9_\-\.]+/)+[a-zA-Z0-9_\-\.]+\.[a-zA-Z0-9]+',
        # Windows-style paths (normalize to Unix)
        r'(?:[a-zA-Z]:\\)?(?:[a-zA-Z0-9_\-\.]+\\)+[a-zA-Z0-9_\-\.]+\.[a-zA-Z0-9]+',
        # Paths in quotes or parentheses
        r'["\']([^"\']+\.(?:py|js|ts|json|md|txt|yml|yaml|toml|ini|cfg))["\']',
        # Paths after "in", "at", "from", "to"
        r'(?:in|at|from|to|file|path|located|found)\s+([a-zA-Z0-9_\-\./\\]+\.(?:py|js|ts|json|md|txt|yml|yaml|toml|ini|cfg))',
    ]
    
    found_paths = set()
    
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            path = match.group(0) if match.lastindex is None else match.group(1)
            if path:
                # Normalize Windows paths to Unix
                path = path.replace('\\', '/')
                # Remove quotes if present
                path = path.strip('"\'')
                # Remove leading/trailing whitespace
                path = path.strip()
                
                # Validate it looks like a file path
                if '/' in path or path.startswith('./') or path.startswith('../'):
                    # Remove common prefixes
                    if path.startswith('./'):
                        path = path[2:]
                    found_paths.add(path)
    
    # Filter out common false positives
    filtered_paths = []
    false_positives = [
        'http://', 'https://', 'www.', 'mailto:', 'ftp://',
        'version', 'python', 'javascript', 'typescript'
    ]
    
    for path in sorted(found_paths):
        # Check if it's a false positive
        is_false_positive = any(
            fp in path.lower() for fp in false_positives
        )
        
        # Must have a file extension
        has_extension = '.' in path and path.split('.')[-1] in [
            'py', 'js', 'ts', 'json', 'md', 'txt', 'yml', 'yaml', 
            'toml', 'ini', 'cfg', 'html', 'css', 'xml'
        ]
        
        if not is_false_positive and has_extension:
            filtered_paths.append(path)
    
    return filtered_paths
