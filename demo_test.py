#!/usr/bin/env python3

"""
Simple demonstration of MCP Server functionality
"""

import sys
import os
import json
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def create_sample_document():
    """Create a sample architecture document for testing"""
    sample_content = """
# Sample Web Application Architecture

## Project Overview
Build a modern web application using Next.js, React, and TypeScript.

## Technology Stack
- Next.js 15
- React 18
- TypeScript
- Tailwind CSS
- Prisma ORM
- SQLite Database

## Setup Instructions

### Initialize Project
npx create-next-app@latest my-app --typescript --tailwind --eslint --app
cd my-app

### Install Dependencies
npm install prisma @prisma/client
npm install zustand framer-motion lucide-react
npm install -D @types/node

### Database Setup
npx prisma init --datasource-provider sqlite
npx prisma generate
npx prisma db push

### File Structure
src/
  app/
    layout.tsx
    page.tsx
    globals.css
  components/
    ui/
  lib/
    db.ts
    utils.ts

## Configuration Files

### package.json
{
  "name": "my-app",
  "version": "0.1.0",
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start"
  }
}

### Database Schema
// prisma/schema.prisma
generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "sqlite"
  url      = "file:./dev.db"
}

model User {
  id    String @id @default(cuid())
  email String @unique
  name  String?
}

## Build Commands
npm run build
npm run start
"""
    
    with open("sample_architecture.md", "w", encoding="utf-8") as f:
        f.write(sample_content)
    
    return "sample_architecture.md"

def demo_mcp_server():
    """Demonstrate MCP Server functionality"""
    print("🚀 MCP Server Functionality Demo\n")
    
    try:
        # Import MCP Server modules
        from mcp_server.ingestion import DocumentProcessor
        from mcp_server.asm import ArchitecturalSynthesisModule
        from mcp_server.builder import CodeGenerationEngine
        
        print("✅ All MCP Server modules imported successfully\n")
        
        # Step 1: Create sample document
        print("📄 Step 1: Creating sample architecture document...")
        doc_path = create_sample_document()
        print(f"✅ Created: {doc_path}\n")
        
        # Step 2: Document Processing
        print("📖 Step 2: Processing document...")
        processor = DocumentProcessor(max_chunk_size=1000)
        chunks = processor.process_file(doc_path)
        
        print(f"✅ Document processed: {len(chunks)} chunks created")
        
        # Show chunk statistics
        chunk_types = {}
        for chunk in chunks:
            chunk_type = chunk.chunk_type
            chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
        
        print("📊 Chunk breakdown:")
        for chunk_type, count in chunk_types.items():
            print(f"   - {chunk_type}: {count} chunks")
        print()
        
        # Step 3: Architectural Synthesis
        print("🧠 Step 3: Architectural synthesis...")
        asm = ArchitecturalSynthesisModule()
        build_plan = asm.synthesize_architecture(chunks)
        
        print(f"✅ Build plan generated:")
        print(f"   - Project: {build_plan.project_name}")
        print(f"   - Description: {build_plan.description}")
        print(f"   - Technologies: {', '.join(build_plan.technology_stack)}")
        print(f"   - Dependencies: {len(build_plan.dependencies)} packages")
        print(f"   - Build instructions: {len(build_plan.build_instructions)} steps")
        
        if build_plan.dependencies:
            print(f"   - Sample dependencies: {', '.join(build_plan.dependencies[:3])}")
        print()
        
        # Step 4: Save Build Plan
        print("💾 Step 4: Saving build plan...")
        build_plan_path = "demo_build_plan.json"
        
        # Convert to dict for JSON serialization
        from dataclasses import asdict
        plan_dict = asdict(build_plan)
        
        with open(build_plan_path, 'w', encoding='utf-8') as f:
            json.dump(plan_dict, f, indent=2, default=str)
        
        print(f"✅ Build plan saved to: {build_plan_path}\n")
        
        # Step 5: Code Generation (Dry Run)
        print("🔨 Step 5: Code generation (dry run)...")
        engine = CodeGenerationEngine(
            working_directory="./demo_output",
            dry_run=True
        )
        
        success = engine.execute_build_plan_object(build_plan)
        
        if success:
            print("✅ Code generation simulation completed successfully\n")
        else:
            print("❌ Code generation simulation failed\n")
            return False
        
        # Step 6: Show Results
        print("📋 Step 6: Summary of generated build plan:")
        print(f"   - Project would be created in: ./demo_output/{build_plan.project_name}")
        print(f"   - {len(build_plan.build_instructions)} build steps would be executed")
        print(f"   - Technologies: {', '.join(build_plan.technology_stack)}")
        
        # Clean up
        if Path(doc_path).exists():
            Path(doc_path).unlink()
        
        return True
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = demo_mcp_server()
    
    if success:
        print("\n🎉 MCP Server Demo Completed Successfully!")
        print("\n✨ Key Features Demonstrated:")
        print("   ✅ Document processing and chunking")
        print("   ✅ Technology stack detection")
        print("   ✅ Dependency extraction")
        print("   ✅ Build plan generation")
        print("   ✅ Code generation engine")
        print("\n🚀 MCP Server is ready for use!")
        exit(0)
    else:
        print("\n❌ Demo failed!")
        exit(1)
