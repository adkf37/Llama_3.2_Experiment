# AI and Machine Learning Facts

## Large Language Models
- Large Language Models (LLMs) like GPT-4, Claude, and Llama are trained on vast amounts of text data to understand and generate human-like responses.
- Llama 3.2 is Meta's latest open-source language model, available in multiple sizes including 1B, 3B, 11B, and 90B parameters.
- Temperature controls the randomness in AI text generation - lower values (0.1-0.3) produce more focused responses, while higher values (0.7-1.0) increase creativity.

## Retrieval Augmented Generation (RAG)
- RAG combines pre-trained language models with external knowledge retrieval to provide more accurate and up-to-date information.
- Vector databases like ChromaDB, Pinecone, and Weaviate store document embeddings for efficient similarity search.
- Embedding models like Sentence-BERT convert text into numerical vectors that capture semantic meaning.

## Model Parameters
- Top-p (nucleus sampling) controls the cumulative probability threshold for token selection.
- Repeat penalty prevents the model from generating repetitive text.
- Context window determines how much previous conversation the model can remember.

## Hardware Requirements
- Running LLMs locally requires significant computational resources - GPUs with large VRAM are preferred.
- Quantization techniques can reduce model size and memory requirements while maintaining performance.
- Apple Silicon Macs can run many open-source models efficiently through Metal Performance Shaders.
