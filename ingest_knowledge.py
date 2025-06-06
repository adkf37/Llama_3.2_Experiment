#!/usr/bin/env python3
"""
Knowledge Base Ingestion Script
Processes files in the knowledge_base directory and adds them to the vector database.
"""

import os
import sys
from pathlib import Path
import argparse

from rag_system import RAGSystem
from config import config

def main():
    """Main ingestion script."""
    parser = argparse.ArgumentParser(description="Ingest knowledge base files")
    parser.add_argument("--path", "-p", help="Path to knowledge base directory")
    parser.add_argument("--clear", action="store_true", help="Clear existing knowledge base first")
    parser.add_argument("--file", "-f", help="Ingest a single file")
    
    args = parser.parse_args()
    
    # Initialize RAG system
    rag_system = RAGSystem()
    
    # Clear existing knowledge base if requested
    if args.clear:
        print("🗑️  Clearing existing knowledge base...")
        rag_system.clear_collection()
    
    # Ingest single file
    if args.file:
        file_path = Path(args.file)
        if file_path.exists():
            print(f"📄 Processing file: {file_path}")
            rag_system.add_document_from_file(str(file_path))
        else:
            print(f"❌ File not found: {file_path}")
            return
    
    # Ingest knowledge base directory
    else:
        knowledge_dir = args.path or config.get('knowledge.base_directory', './knowledge_base')
        print(f"📚 Ingesting knowledge base from: {knowledge_dir}")
        rag_system.ingest_knowledge_base(knowledge_dir)
    
    # Show final stats
    info = rag_system.get_collection_info()
    print(f"\n✅ Knowledge base now contains {info['document_count']} documents")

if __name__ == "__main__":
    main()
