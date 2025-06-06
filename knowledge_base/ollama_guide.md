# Ollama Setup and Usage Guide

## What is Ollama?
Ollama is a tool that allows you to run large language models locally on your machine. It provides a simple API to interact with various open-source models including Llama, Mistral, and Code Llama.

## Installation
- Windows: Download from https://ollama.ai/ or use `winget install Ollama.Ollama`
- macOS: Download from the website or use `brew install ollama`
- Linux: Use the installation script or package managers

## Basic Commands
- `ollama pull <model>` - Download a model
- `ollama run <model>` - Run a model interactively
- `ollama list` - List installed models
- `ollama rm <model>` - Remove a model
- `ollama serve` - Start the Ollama server

## Popular Models
- llama3.2:1b - Fastest, smallest Llama 3.2 model
- llama3.2:3b - Balanced performance and speed
- llama3.2:11b - Higher quality responses
- llama3.2:90b - Largest, highest quality (requires significant resources)
- codellama - Specialized for code generation
- mistral - Fast and efficient general-purpose model

## API Usage
Ollama provides a REST API on localhost:11434 that can be used to integrate with applications. The API supports streaming responses and various model parameters.

## Performance Tips
- Use GPU acceleration when available
- Adjust context length based on your needs
- Consider quantized models for better performance on limited hardware
- Monitor memory usage to prevent system slowdowns
