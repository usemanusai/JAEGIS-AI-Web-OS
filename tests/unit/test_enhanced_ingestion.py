"""
Unit tests for enhanced document ingestion module.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from mcp_server.enhanced_ingestion import EnhancedDocumentProcessor, DocumentChunk


class TestEnhancedDocumentProcessor:
    """Test cases for EnhancedDocumentProcessor."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.processor = EnhancedDocumentProcessor()
    
    def test_initialization(self):
        """Test processor initialization."""
        assert self.processor.max_chunk_size == 4000
        assert self.processor.chunk_overlap_size == 200
        assert isinstance(self.processor.supported_formats, list)
        assert '.docx' in self.processor.supported_formats
    
    def test_initialization_with_custom_params(self):
        """Test processor initialization with custom parameters."""
        processor = EnhancedDocumentProcessor(
            max_chunk_size=2000,
            chunk_overlap_size=100
        )
        assert processor.max_chunk_size == 2000
        assert processor.chunk_overlap_size == 100
    
    def test_format_detection_docx(self):
        """Test format detection for DOCX files."""
        result = self.processor._detect_format("test.docx")
        assert result == "docx"
    
    def test_format_detection_pdf(self):
        """Test format detection for PDF files."""
        result = self.processor._detect_format("test.pdf")
        assert result == "pdf"
    
    def test_format_detection_markdown(self):
        """Test format detection for Markdown files."""
        result = self.processor._detect_format("test.md")
        assert result == "markdown"
    
    def test_format_detection_unsupported(self):
        """Test format detection for unsupported files."""
        result = self.processor._detect_format("test.xyz")
        assert result == "unknown"
    
    @patch('pathlib.Path.exists')
    def test_process_file_enhanced_file_not_found(self, mock_exists):
        """Test processing non-existent file."""
        mock_exists.return_value = False
        
        with pytest.raises(FileNotFoundError):
            self.processor.process_file_enhanced("nonexistent.docx")
    
    def test_semantic_chunking_basic(self):
        """Test basic semantic chunking functionality."""
        content = "This is a test document. " * 100  # Create long content
        chunks = self.processor._semantic_chunking(content)
        
        assert len(chunks) > 0
        assert all(isinstance(chunk, DocumentChunk) for chunk in chunks)
        assert all(len(chunk.content) <= self.processor.max_chunk_size for chunk in chunks)
    
    def test_semantic_chunking_short_content(self):
        """Test semantic chunking with short content."""
        content = "Short content that fits in one chunk."
        chunks = self.processor._semantic_chunking(content)
        
        assert len(chunks) == 1
        assert chunks[0].content == content
    
    def test_extract_entities_basic(self):
        """Test basic entity extraction."""
        content = "This project uses React, Node.js, and PostgreSQL database."
        entities = self.processor._extract_entities(content)
        
        assert 'technologies' in entities
        assert 'dependencies' in entities
        assert len(entities['technologies']) > 0
    
    def test_extract_entities_empty_content(self):
        """Test entity extraction with empty content."""
        entities = self.processor._extract_entities("")
        
        assert 'technologies' in entities
        assert 'dependencies' in entities
        assert len(entities['technologies']) == 0
        assert len(entities['dependencies']) == 0
    
    @patch('mcp_server.enhanced_ingestion.docx.Document')
    def test_process_docx_success(self, mock_document):
        """Test successful DOCX processing."""
        # Mock document structure
        mock_para = Mock()
        mock_para.text = "Test paragraph content"
        mock_document.return_value.paragraphs = [mock_para]
        
        with patch('pathlib.Path.exists', return_value=True):
            result = self.processor._process_docx("test.docx")
            
        assert "Test paragraph content" in result
    
    @patch('mcp_server.enhanced_ingestion.fitz.open')
    def test_process_pdf_success(self, mock_fitz):
        """Test successful PDF processing."""
        # Mock PDF structure
        mock_page = Mock()
        mock_page.get_text.return_value = "Test PDF content"
        mock_doc = Mock()
        mock_doc.__iter__ = Mock(return_value=iter([mock_page]))
        mock_fitz.return_value = mock_doc
        
        with patch('pathlib.Path.exists', return_value=True):
            result = self.processor._process_pdf("test.pdf")
            
        assert "Test PDF content" in result
    
    def test_process_markdown_success(self):
        """Test successful Markdown processing."""
        test_content = "# Test Markdown\n\nThis is test content."
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.read_text', return_value=test_content):
            result = self.processor._process_markdown("test.md")
            
        assert "Test Markdown" in result
        assert "This is test content" in result
    
    def test_process_text_success(self):
        """Test successful text processing."""
        test_content = "This is plain text content."
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.read_text', return_value=test_content):
            result = self.processor._process_text("test.txt")
            
        assert result == test_content
    
    def test_document_chunk_creation(self):
        """Test DocumentChunk creation and properties."""
        chunk = DocumentChunk(
            content="Test content",
            chunk_id="test-1",
            start_index=0,
            end_index=12,
            metadata={"test": "value"}
        )
        
        assert chunk.content == "Test content"
        assert chunk.chunk_id == "test-1"
        assert chunk.start_index == 0
        assert chunk.end_index == 12
        assert chunk.metadata["test"] == "value"
    
    def test_error_handling_invalid_format(self):
        """Test error handling for invalid file formats."""
        with patch('pathlib.Path.exists', return_value=True):
            with pytest.raises(ValueError, match="Unsupported file format"):
                self.processor.process_file_enhanced("test.xyz")
    
    @patch('mcp_server.enhanced_ingestion.logger')
    def test_logging_on_error(self, mock_logger):
        """Test that errors are properly logged."""
        with patch('pathlib.Path.exists', return_value=True), \
             patch.object(self.processor, '_process_docx', side_effect=Exception("Test error")):
            
            with pytest.raises(Exception):
                self.processor.process_file_enhanced("test.docx")
            
            mock_logger.error.assert_called()


class TestDocumentChunk:
    """Test cases for DocumentChunk class."""
    
    def test_document_chunk_str_representation(self):
        """Test string representation of DocumentChunk."""
        chunk = DocumentChunk(
            content="Test content",
            chunk_id="test-1"
        )
        
        str_repr = str(chunk)
        assert "test-1" in str_repr
        assert "Test content" in str_repr
    
    def test_document_chunk_equality(self):
        """Test DocumentChunk equality comparison."""
        chunk1 = DocumentChunk(content="Test", chunk_id="1")
        chunk2 = DocumentChunk(content="Test", chunk_id="1")
        chunk3 = DocumentChunk(content="Different", chunk_id="1")
        
        assert chunk1 == chunk2
        assert chunk1 != chunk3
    
    def test_document_chunk_metadata_default(self):
        """Test DocumentChunk with default metadata."""
        chunk = DocumentChunk(content="Test", chunk_id="1")
        assert chunk.metadata == {}
    
    def test_document_chunk_metadata_custom(self):
        """Test DocumentChunk with custom metadata."""
        metadata = {"source": "test.docx", "page": 1}
        chunk = DocumentChunk(content="Test", chunk_id="1", metadata=metadata)
        assert chunk.metadata == metadata
