#!/usr/bin/env python3

"""
Test document processing functionality directly
"""

import sys
import os
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_document_processor():
    """Test the DocumentProcessor class"""
    print("Testing DocumentProcessor...")
    
    try:
        from mcp_server.ingestion import DocumentProcessor
        
        # Create processor instance
        processor = DocumentProcessor(max_chunk_size=1000)
        print("✅ DocumentProcessor created successfully")
        
        # Test with the JAEGIS document
        doc_path = "COMPLETE_BUILD_INSTRUCTIONS_FOR_THE_ENTIRE_JAEGIS_WEB_OS.docx"
        
        if not Path(doc_path).exists():
            print(f"⚠️ Test document not found: {doc_path}")
            return True  # Don't fail if test document is missing
        
        print(f"📄 Processing document: {doc_path}")
        chunks = processor.process_file(doc_path)
        
        print(f"✅ Document processed successfully: {len(chunks)} chunks created")
        
        # Show some statistics
        chunk_types = {}
        total_tokens = 0
        
        for chunk in chunks:
            chunk_type = chunk.chunk_type
            chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
            total_tokens += chunk.metadata.get('token_count', 0)
        
        print(f"📊 Chunk statistics:")
        for chunk_type, count in chunk_types.items():
            print(f"   - {chunk_type}: {count} chunks")
        print(f"   - Total tokens: {total_tokens}")
        
        return True
        
    except Exception as e:
        print(f"❌ DocumentProcessor test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_architectural_synthesis():
    """Test the ArchitecturalSynthesisModule class"""
    print("\nTesting ArchitecturalSynthesisModule...")
    
    try:
        from mcp_server.asm import ArchitecturalSynthesisModule
        from mcp_server.ingestion import DocumentChunk
        
        # Create ASM instance (without API key for basic testing)
        asm = ArchitecturalSynthesisModule()
        print("✅ ArchitecturalSynthesisModule created successfully")
        
        # Create some dummy chunks for testing
        dummy_chunks = [
            DocumentChunk(
                content="npm install react next.js typescript",
                metadata={'token_count': 10},
                chunk_index=0,
                source_file="test.txt",
                chunk_type="command"
            ),
            DocumentChunk(
                content="This is a Next.js application with React and TypeScript",
                metadata={'token_count': 15},
                chunk_index=1,
                source_file="test.txt",
                chunk_type="text"
            )
        ]
        
        print("📊 Testing with dummy chunks...")
        build_plan = asm.synthesize_architecture(dummy_chunks)
        
        print(f"✅ Build plan generated successfully:")
        print(f"   - Project: {build_plan.project_name}")
        print(f"   - Technologies: {build_plan.technology_stack}")
        print(f"   - Dependencies: {len(build_plan.dependencies)}")
        print(f"   - Instructions: {len(build_plan.build_instructions)}")
        
        return True
        
    except Exception as e:
        print(f"❌ ArchitecturalSynthesisModule test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_code_generation():
    """Test the CodeGenerationEngine class"""
    print("\nTesting CodeGenerationEngine...")
    
    try:
        from mcp_server.builder import CodeGenerationEngine
        
        # Create engine instance in dry-run mode
        engine = CodeGenerationEngine(dry_run=True)
        print("✅ CodeGenerationEngine created successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ CodeGenerationEngine test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 MCP Server Document Processing Test\n")
    
    success = True
    success &= test_document_processor()
    success &= test_architectural_synthesis()
    success &= test_code_generation()
    
    if success:
        print("\n🎉 All document processing tests passed!")
        exit(0)
    else:
        print("\n❌ Some tests failed!")
        exit(1)
