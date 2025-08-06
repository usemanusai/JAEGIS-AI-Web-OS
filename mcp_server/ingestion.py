"""
Document Processing Pipeline

Handles ingestion of multiple file formats (.docx, .pdf, .md, .txt)
and prepares content for architectural synthesis.
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

import docx
import PyPDF2
import markdown
from loguru import logger
import tiktoken


@dataclass
class DocumentChunk:
    """Represents a processed chunk of document content."""
    content: str
    metadata: Dict[str, Any]
    chunk_index: int
    source_file: str
    chunk_type: str  # 'text', 'code', 'config', 'command'


class DocumentProcessor:
    """Main document processing pipeline."""
    
    def __init__(self, max_chunk_size: int = 4000):
        self.max_chunk_size = max_chunk_size
        self.encoding = tiktoken.get_encoding("cl100k_base")
        
    def process_file(self, file_path: str) -> List[DocumentChunk]:
        """Process a single file and return structured chunks."""
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        logger.info(f"Processing file: {file_path}")

        # Detect actual file format and extract content
        content = self._extract_content_with_fallback(file_path)

        # Process and chunk the content
        return self._chunk_content(content, str(file_path))

    def _extract_content_with_fallback(self, file_path: Path) -> str:
        """Extract content with robust format detection and fallback mechanisms."""
        file_extension = file_path.suffix.lower()

        # Try format-specific extraction first
        if file_extension == '.docx':
            try:
                return self._extract_docx(file_path)
            except Exception as e:
                logger.warning(f"DOCX extraction failed: {e}. Trying text fallback...")
                return self._extract_text_with_encoding_detection(file_path)

        elif file_extension == '.pdf':
            try:
                return self._extract_pdf(file_path)
            except Exception as e:
                logger.warning(f"PDF extraction failed: {e}. Trying text fallback...")
                return self._extract_text_with_encoding_detection(file_path)

        elif file_extension == '.md':
            return self._extract_markdown(file_path)

        elif file_extension == '.txt':
            return self._extract_text_with_encoding_detection(file_path)

        else:
            # For unknown extensions, try to detect content type
            logger.warning(f"Unknown file extension: {file_extension}. Attempting content detection...")
            return self._extract_text_with_encoding_detection(file_path)
    
    def _extract_docx(self, file_path: Path) -> str:
        """Extract text from DOCX file."""
        try:
            doc = docx.Document(file_path)
            content = []
            
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    content.append(paragraph.text)
                    
            return '\n'.join(content)
        except Exception as e:
            logger.error(f"Error extracting DOCX: {e}")
            raise
    
    def _extract_pdf(self, file_path: Path) -> str:
        """Extract text from PDF file."""
        try:
            content = []
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                for page in pdf_reader.pages:
                    text = page.extract_text()
                    if text.strip():
                        content.append(text)
                        
            return '\n'.join(content)
        except Exception as e:
            logger.error(f"Error extracting PDF: {e}")
            raise
    
    def _extract_markdown(self, file_path: Path) -> str:
        """Extract text from Markdown file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            logger.error(f"Error extracting Markdown: {e}")
            raise
    
    def _extract_text(self, file_path: Path) -> str:
        """Extract text from plain text file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            logger.error(f"Error extracting text: {e}")
            raise

    def _extract_text_with_encoding_detection(self, file_path: Path) -> str:
        """Extract text with automatic encoding detection."""
        import chardet

        try:
            # Read file in binary mode to detect encoding
            with open(file_path, 'rb') as file:
                raw_data = file.read()

            # Detect encoding
            encoding_result = chardet.detect(raw_data)
            detected_encoding = encoding_result.get('encoding', 'utf-8')
            confidence = encoding_result.get('confidence', 0)

            logger.debug(f"Detected encoding: {detected_encoding} (confidence: {confidence:.2f})")

            # Try detected encoding first
            try:
                content = raw_data.decode(detected_encoding)
                return content
            except UnicodeDecodeError:
                logger.warning(f"Failed to decode with detected encoding {detected_encoding}")

            # Fallback to common encodings
            for encoding in ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']:
                try:
                    content = raw_data.decode(encoding)
                    logger.info(f"Successfully decoded with fallback encoding: {encoding}")
                    return content
                except UnicodeDecodeError:
                    continue

            # Last resort: decode with errors='replace'
            content = raw_data.decode('utf-8', errors='replace')
            logger.warning("Used UTF-8 with error replacement for decoding")
            return content

        except Exception as e:
            logger.error(f"Error extracting text with encoding detection: {e}")
            raise
    
    def _chunk_content(self, content: str, source_file: str) -> List[DocumentChunk]:
        """Split content into manageable chunks for AI processing."""
        chunks = []
        
        # Split content into logical sections
        sections = self._split_into_sections(content)
        
        chunk_index = 0
        for section in sections:
            # Determine chunk type
            chunk_type = self._classify_chunk_type(section)
            
            # Split large sections into smaller chunks
            if self._count_tokens(section) > self.max_chunk_size:
                sub_chunks = self._split_large_section(section)
                for sub_chunk in sub_chunks:
                    chunks.append(DocumentChunk(
                        content=sub_chunk,
                        metadata={
                            'token_count': self._count_tokens(sub_chunk),
                            'section_type': chunk_type
                        },
                        chunk_index=chunk_index,
                        source_file=source_file,
                        chunk_type=chunk_type
                    ))
                    chunk_index += 1
            else:
                chunks.append(DocumentChunk(
                    content=section,
                    metadata={
                        'token_count': self._count_tokens(section),
                        'section_type': chunk_type
                    },
                    chunk_index=chunk_index,
                    source_file=source_file,
                    chunk_type=chunk_type
                ))
                chunk_index += 1
                
        logger.info(f"Created {len(chunks)} chunks from {source_file}")
        return chunks
    
    def _split_into_sections(self, content: str) -> List[str]:
        """Split content into logical sections."""
        # Split by common section markers
        section_patterns = [
            r'\n#{1,6}\s+',  # Markdown headers
            r'\nTask \d+',   # Task sections
            r'\nPhase \d+',  # Phase sections
            r'\nSubtask \d+', # Subtask sections
            r'\n\n(?=[A-Z])', # Double newline followed by capital letter
        ]
        
        sections = [content]
        for pattern in section_patterns:
            new_sections = []
            for section in sections:
                parts = re.split(pattern, section)
                new_sections.extend([part.strip() for part in parts if part.strip()])
            sections = new_sections
            
        return sections
    
    def _classify_chunk_type(self, content: str) -> str:
        """Classify the type of content in a chunk."""
        content_lower = content.lower()
        
        # Check for code blocks
        if '```' in content or content.startswith('//') or content.startswith('#'):
            return 'code'
        
        # Check for configuration files
        if any(ext in content_lower for ext in ['.json', '.yaml', '.yml', '.toml', '.env']):
            return 'config'
        
        # Check for shell commands
        if any(cmd in content_lower for cmd in ['npm install', 'npx', 'cd ', 'mkdir', 'git ']):
            return 'command'
            
        return 'text'
    
    def _split_large_section(self, section: str) -> List[str]:
        """Split a large section into smaller chunks."""
        sentences = re.split(r'(?<=[.!?])\s+', section)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            test_chunk = current_chunk + " " + sentence if current_chunk else sentence
            
            if self._count_tokens(test_chunk) > self.max_chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                current_chunk = test_chunk
                
        if current_chunk:
            chunks.append(current_chunk.strip())
            
        return chunks
    
    def _count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken."""
        return len(self.encoding.encode(text))
    
    def process_multiple_files(self, file_paths: List[str]) -> Dict[str, List[DocumentChunk]]:
        """Process multiple files and return organized chunks."""
        results = {}
        
        for file_path in file_paths:
            try:
                chunks = self.process_file(file_path)
                results[file_path] = chunks
            except Exception as e:
                logger.error(f"Failed to process {file_path}: {e}")
                results[file_path] = []
                
        return results
