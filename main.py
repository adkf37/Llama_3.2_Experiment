#!/usr/bin/env python3
"""
Llama 3.2 RAG System - Main Application
"""

import os
import sys
from pathlib import Path
from typing import Optional
import argparse

from llama_client import LlamaClient
from rag_system import RAGSystem
from config import config

class LlamaRAGApp:
    """Main application class for Llama RAG system."""
    
    def __init__(self):
        self.llama_client = LlamaClient()
        self.rag_system = RAGSystem()
        self.setup_knowledge_base()
    
    def setup_knowledge_base(self):
        """Setup and ingest knowledge base if auto_ingest is enabled."""
        if config.get('knowledge.auto_ingest', True):
            print("🔄 Setting up knowledge base...")
            self.rag_system.ingest_knowledge_base()
            
            # Show collection info
            info = self.rag_system.get_collection_info()
            print(f"📚 Knowledge base: {info['document_count']} documents loaded")
    
    def ask_question(self, question: str, use_rag: bool = True, temperature: Optional[float] = None) -> str:
        """Ask a question with optional RAG enhancement."""
        print(f"\n🤔 Question: {question}")
        
        if use_rag:
            # Get relevant context
            context = self.rag_system.get_relevant_context(question)
            
            if context:
                print(f"📖 Found {len(context)} relevant context documents")
                response = self.llama_client.generate_with_context(
                    prompt=question,
                    context=context,
                    temperature=temperature
                )
            else:
                print("📖 No relevant context found, using base model")
                response = self.llama_client.generate(
                    prompt=question,
                    temperature=temperature
                )
        else:
            print("🤖 Using base model (no RAG)")
            response = self.llama_client.generate(
                prompt=question,
                temperature=temperature
            )
        
        return response
    
    def add_fact(self, fact: str, source: str = "manual") -> None:
        """Add a new fact to the knowledge base."""
        self.rag_system.add_documents(
            documents=[fact],
            metadata=[{"source": source, "type": "fact"}]
        )
        print(f"✅ Added fact to knowledge base: {fact[:100]}...")
    
    def interactive_mode(self):
        """Run the application in interactive mode."""
        print("🦙 Llama 3.2 RAG System - Interactive Mode")
        print("=" * 50)
        
        # Show current configuration
        print(f"Model: {config.get('model.name')}")
        print(f"Temperature: {config.get('model.temperature')}")
        print(f"Max tokens: {config.get('model.max_tokens')}")
        
        # Show knowledge base info
        info = self.rag_system.get_collection_info()
        print(f"Knowledge base: {info['document_count']} documents")
        print("\nCommands:")
        print("  /help - Show this help")
        print("  /config - Show current configuration")
        print("  /temp <value> - Set temperature (0.0-2.0)")
        print("  /add <fact> - Add a fact to knowledge base")
        print("  /norag <question> - Ask without RAG")
        print("  /info - Show knowledge base info")
        print("  /quit - Exit")
        print("-" * 50)
        
        current_temp = config.get('model.temperature')
        
        while True:
            try:
                user_input = input("\n💬 You: ").strip()
                
                if not user_input:
                    continue
                
                # Handle commands
                if user_input.startswith('/'):
                    parts = user_input.split(' ', 1)
                    command = parts[0].lower()
                    
                    if command == '/help':
                        print("\nCommands:")
                        print("  /help - Show this help")
                        print("  /config - Show current configuration")
                        print("  /temp <value> - Set temperature (0.0-2.0)")
                        print("  /add <fact> - Add a fact to knowledge base")
                        print("  /norag <question> - Ask without RAG")
                        print("  /info - Show knowledge base info")
                        print("  /quit - Exit")
                    
                    elif command == '/config':
                        print(f"\nCurrent Configuration:")
                        print(f"  Model: {config.get('model.name')}")
                        print(f"  Temperature: {current_temp}")
                        print(f"  Max tokens: {config.get('model.max_tokens')}")
                        print(f"  Top-p: {config.get('model.top_p')}")
                    
                    elif command == '/temp':
                        if len(parts) > 1:
                            try:
                                new_temp = float(parts[1])
                                if 0.0 <= new_temp <= 2.0:
                                    current_temp = new_temp
                                    print(f"🌡️  Temperature set to {current_temp}")
                                else:
                                    print("❌ Temperature must be between 0.0 and 2.0")
                            except ValueError:
                                print("❌ Invalid temperature value")
                        else:
                            print(f"Current temperature: {current_temp}")
                    
                    elif command == '/add':
                        if len(parts) > 1:
                            self.add_fact(parts[1])
                        else:
                            print("❌ Please provide a fact to add")
                    
                    elif command == '/norag':
                        if len(parts) > 1:
                            response = self.ask_question(parts[1], use_rag=False, temperature=current_temp)
                            print(f"\n🤖 Assistant: {response}")
                        else:
                            print("❌ Please provide a question")
                    
                    elif command == '/info':
                        info = self.rag_system.get_collection_info()
                        print(f"\n📊 Knowledge Base Info:")
                        print(f"  Documents: {info['document_count']}")
                        print(f"  Collection: {info['collection_name']}")
                        print(f"  Embedding model: {info['embedding_model']}")
                    
                    elif command == '/quit':
                        print("👋 Goodbye!")
                        break
                    
                    else:
                        print("❌ Unknown command. Type /help for available commands.")
                
                else:
                    # Regular question
                    response = self.ask_question(user_input, use_rag=True, temperature=current_temp)
                    print(f"\n🤖 Assistant: {response}")
            
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Llama 3.2 RAG System")
    parser.add_argument("--question", "-q", help="Ask a single question and exit")
    parser.add_argument("--no-rag", action="store_true", help="Disable RAG for this question")
    parser.add_argument("--temperature", "-t", type=float, help="Set temperature (0.0-2.0)")
    parser.add_argument("--setup", action="store_true", help="Setup mode - pull model and exit")
    
    args = parser.parse_args()
    
    # Setup mode
    if args.setup:
        print("🔧 Setup Mode")
        client = LlamaClient()
        model_name = config.get('model.name', 'llama3.2')
        client.pull_model(model_name)
        return
    
    # Initialize app
    try:
        app = LlamaRAGApp()
    except Exception as e:
        print(f"❌ Failed to initialize application: {e}")
        print("💡 Try running with --setup first to pull the model")
        return
    
    # Single question mode
    if args.question:
        use_rag = not args.no_rag
        response = app.ask_question(args.question, use_rag=use_rag, temperature=args.temperature)
        print(f"\n🤖 Assistant: {response}")
        return
    
    # Interactive mode
    app.interactive_mode()

if __name__ == "__main__":
    main()
