# Llama 3.2 Local RAG Setup

This project sets up a local Llama 3.2 instance with Retrieval Augmented Generation (RAG) capabilities.

## Features

- **Local Llama 3.2 Model**: Running via Ollama
- **RAG System**: Store and retrieve additional facts to enhance responses
- **Configurable Parameters**: Temperature, top-p, max tokens, etc.
- **Vector Database**: ChromaDB for efficient similarity search
- **Interactive Interface**: Command-line and web interface options

## Quick Start

1. **Install Ollama** (if not already installed):
   ```powershell
   # Download from https://ollama.ai/ or use winget
   winget install Ollama.Ollama
   ```

2. **Install Python Dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```

3. **Pull Llama 3.2 Model**:
   ```powershell
   ollama pull llama3.2
   ```

4. **Run the RAG System**:
   ```powershell
   python main.py
   ```

## Project Structure

- `main.py` - Main application entry point
- `rag_system.py` - RAG implementation with vector database
- `llama_client.py` - Ollama client wrapper
- `config.py` - Configuration management
- `knowledge_base/` - Directory for storing facts and documents
- `data/` - Vector database storage
- `requirements.txt` - Python dependencies

## Configuration

Edit `config.yaml` to customize:
- Model parameters (temperature, top_p, etc.)
- RAG settings (chunk size, similarity threshold)
- Vector database settings

## Adding Knowledge

Place text files in the `knowledge_base/` directory and run:
```powershell
python ingest_knowledge.py
```
