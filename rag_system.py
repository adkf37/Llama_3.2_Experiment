import os
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Optional
from pathlib import Path
import json
from config import config

class RAGSystem:
    """Retrieval Augmented Generation system using ChromaDB."""
    
    def __init__(self):
        self.config = config
        self.embedding_model = SentenceTransformer(
            self.config.get('rag.embedding_model', 'all-MiniLM-L6-v2')
        )
        
        # Initialize ChromaDB
        persist_dir = self.config.get('vectordb.persist_directory', './data/chroma_db')
        os.makedirs(persist_dir, exist_ok=True)
        
        self.chroma_client = chromadb.PersistentClient(path=persist_dir)
        self.collection_name = self.config.get('vectordb.collection_name', 'knowledge_base')
        
        # Get or create collection
        try:
            self.collection = self.chroma_client.get_collection(name=self.collection_name)
        except:
            self.collection = self.chroma_client.create_collection(
                name=self.collection_name,
                metadata={"description": "Knowledge base for RAG system"}
            )
    
    def add_documents(self, documents: List[str], metadata: Optional[List[Dict[str, Any]]] = None, ids: Optional[List[str]] = None) -> None:
        """Add documents to the vector database."""
        if not documents:
            return
        
        # Generate embeddings
        embeddings = self.embedding_model.encode(documents).tolist()
        
        # Generate IDs if not provided
        if ids is None:
            existing_count = self.collection.count()
            ids = [f"doc_{existing_count + i}" for i in range(len(documents))]
          # Prepare metadata - convert to proper format
        if metadata is None:
            metadata = [{"source": "manual_add"} for _ in documents]
        
        # Convert metadata to the format expected by ChromaDB
        formatted_metadata = []
        for meta in metadata:
            formatted_meta = {}
            for key, value in meta.items():
                if isinstance(value, (str, int, float, bool)) or value is None:
                    formatted_meta[key] = value
                else:
                    formatted_meta[key] = str(value)
            formatted_metadata.append(formatted_meta)
        
        # Add to collection
        self.collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=formatted_metadata,
            ids=ids
        )
        
        print(f"✅ Added {len(documents)} documents to knowledge base")
    
    def add_document_from_file(self, file_path: str) -> None:
        """Add a document from a file."""
        file_path_obj = Path(file_path)
        
        if not file_path_obj.exists():
            raise FileNotFoundError(f"File not found: {file_path_obj}")
        
        # Read file content
        with open(file_path_obj, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split into chunks
        chunks = self._split_text(content)
        
        # Prepare metadata
        metadata = [{
            "source": str(file_path_obj),
            "filename": file_path_obj.name,
            "chunk_index": i
        } for i in range(len(chunks))]
        
        # Generate IDs
        base_id = file_path_obj.stem
        ids = [f"{base_id}_chunk_{i}" for i in range(len(chunks))]
        
        self.add_documents(chunks, metadata, ids)
    
    def _split_text(self, text: str) -> List[str]:
        """Split text into chunks for processing."""
        chunk_size = self.config.get('rag.chunk_size', 500)
        chunk_overlap = self.config.get('rag.chunk_overlap', 50)
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            
            # Try to break at word boundaries
            if end < len(text):
                last_space = chunk.rfind(' ')
                if last_space > chunk_size * 0.8:  # If we can find a reasonable break point
                    chunk = chunk[:last_space]
                    end = start + last_space
            
            chunks.append(chunk.strip())
            start = end - chunk_overlap
            
            if start >= len(text):
                break
        
        return [chunk for chunk in chunks if chunk.strip()]

    def query(self, query: str, n_results: Optional[int] = None) -> List[Dict[str, Any]]:
        """Query the knowledge base for relevant documents."""
        if n_results is None:
            n_results = self.config.get('rag.max_retrieved_docs', 5)
        
        # Generate query embedding
        query_embedding = self.embedding_model.encode([query]).tolist()[0]
          # Search in collection
        actual_n_results = n_results if n_results is not None else 5
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=actual_n_results
        )
          # Format results
        formatted_results = []
        if results and 'documents' in results and results['documents'] and results['documents'][0]:
            for i, doc in enumerate(results['documents'][0]):
                metadata = {}
                distance = 0
                doc_id = f"result_{i}"
                
                if 'metadatas' in results and results['metadatas'] and len(results['metadatas']) > 0 and len(results['metadatas'][0]) > i:
                    metadata = results['metadatas'][0][i] or {}
                
                if 'distances' in results and results['distances'] and len(results['distances']) > 0 and len(results['distances'][0]) > i:
                    distance = results['distances'][0][i] or 0
                
                if 'ids' in results and results['ids'] and len(results['ids']) > 0 and len(results['ids'][0]) > i:
                    doc_id = results['ids'][0][i] or f"result_{i}"
                
                formatted_results.append({
                    'content': doc,
                    'metadata': metadata,
                    'distance': distance,
                    'id': doc_id
                })
        
        return formatted_results
    
    def get_relevant_context(self, query: str) -> List[str]:
        """Get relevant context for a query, filtered by similarity threshold."""
        results = self.query(query)
        threshold = self.config.get('rag.similarity_threshold', 0.7)
        
        # Filter by similarity (lower distance = higher similarity)
        relevant_docs = []
        for result in results:
            # Convert distance to similarity (assuming cosine distance)
            similarity = 1 - result['distance']
            if similarity >= threshold:
                relevant_docs.append(result['content'])
        
        return relevant_docs
    
    def ingest_knowledge_base(self, knowledge_dir_param: Optional[str] = None) -> None:
        """Ingest all files from the knowledge base directory."""
        effective_knowledge_dir: str
        if knowledge_dir_param is not None:
            effective_knowledge_dir = knowledge_dir_param
        else:
            # Get from config, ensuring it's not None
            conf_val = self.config.get('knowledge.base_directory', './knowledge_base')
            if conf_val is None:
                print("⚠️ Knowledge base directory not found in config or is null, using default './knowledge_base'")
                effective_knowledge_dir = './knowledge_base'
            else:
                effective_knowledge_dir = str(conf_val) # Ensure it's a string
        
        knowledge_path = Path(effective_knowledge_dir)
        if not knowledge_path.exists():
            os.makedirs(knowledge_path, exist_ok=True)
            print(f"📁 Created knowledge base directory: {knowledge_path}")
            return
        
        supported_formats = self.config.get('knowledge.supported_formats', ['.txt', '.md'])
        
        files_processed = 0
        for file_path in knowledge_path.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in supported_formats:
                try:
                    self.add_document_from_file(str(file_path))
                    files_processed += 1
                except Exception as e:
                    print(f"❌ Error processing {file_path}: {e}")
        
        print(f"✅ Processed {files_processed} files from knowledge base")
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the current collection."""
        count = self.collection.count()
        return {
            'collection_name': self.collection_name,
            'document_count': count,
            'embedding_model': self.config.get('rag.embedding_model', 'all-MiniLM-L6-v2')
        }
    
    def clear_collection(self) -> None:
        """Clear all documents from the collection."""
        # Delete and recreate collection
        self.chroma_client.delete_collection(name=self.collection_name)
        self.collection = self.chroma_client.create_collection(
            name=self.collection_name,
            metadata={"description": "Knowledge base for RAG system"}
        )
        print("🗑️  Cleared all documents from knowledge base")
