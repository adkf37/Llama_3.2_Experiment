import ollama
from ollama._types import Options
from typing import List, Dict, Any, Optional, Union, cast
from config import config
from prompt_registry import build_tool_system_prompt
import json

class LlamaClient:
    """Client for interacting with Llama models via Ollama."""
    
    def __init__(self, model_name: Optional[str] = None):
        self.config = config
        self.model_name = model_name or self.config.get('model.name', 'llama3.2:3b')
        self.system_prompt_variant = self.config.get('prompts.system_prompt_variant', 'tool_use_v1')
        self.client = ollama.Client()
        
        # Check if model is available
        if not self._check_model_availability():
            print(f"⚠️  Model {self.model_name} not found. Please pull it with: ollama pull {self.model_name}")

    def _check_model_availability(self) -> bool:
        """Check if the specified model is available locally."""
        try:
            models_response = self.client.list()
            print(f"🔍 Debug: models response structure: {models_response}")  # Add debug line
            
            # Handle the ListResponse object from Ollama
            if hasattr(models_response, 'models'):
                # Extract model names from the Model objects
                available_models = [model.model for model in models_response.models]
            else:
                print(f"🔍 Debug: Unexpected models structure: {type(models_response)}")
                return False
            
            # Filter out empty names
            available_models = [name for name in available_models if name]
            
            print(f"🔍 Available models: {available_models}")  # Add debug line
            print(f"🔍 Looking for: {self.model_name}")  # Add debug line
            
            if self.model_name not in available_models:
                print(f"⚠️  Model {self.model_name} not found. Available models:")
                for model in available_models:
                    print(f"  📦 {model}")
                print(f"To download the model, run: ollama pull {self.model_name}")
                return False
            return True
        except Exception as e:
            print(f"❌ Error checking model availability: {e}")
            print(f"🔍 Debug: Exception type: {type(e)}")  # Add debug line
            return False

    def generate_with_tools(self, prompt: str, tools: List[Dict[str, Any]], 
                          temperature: Optional[float] = None,
                          max_tokens: Optional[int] = None) -> Dict[str, Any]:
        """Generate response with tool calling capability."""
        temperature = temperature or self.config.get('model.temperature', 0.7)
        max_tokens = max_tokens or self.config.get('model.max_tokens', 2048)
        
        system_prompt = build_tool_system_prompt(self.system_prompt_variant, tools)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]

        try:
            typed_options = cast(Options, {
                'temperature': temperature,
                'num_predict': max_tokens,
                'top_p': self.config.get('model.top_p', 0.9),
                'repeat_penalty': self.config.get('model.repeat_penalty', 1.1)
            })

            response = self.client.chat(
                model=self.model_name,
                messages=messages,
                stream=False,
                options=typed_options
            )
            
            return {
                "content": response['message']['content'],
                "needs_tool_call": "TOOL_CALL:" in response['message']['content']
            }
            
        except Exception as e:
            return {"content": f"❌ Error generating response: {e}", "needs_tool_call": False}

    def generate(self, prompt: str,
                 temperature: Optional[float] = None,
                 max_tokens: Optional[int] = None,
                 stream: bool = False) -> Union[str, Any]:
        """Generate a response from the model."""
        temperature = temperature or self.config.get('model.temperature', 0.7)
        max_tokens = max_tokens or self.config.get('model.max_tokens', 2048)
        
        try:
            typed_options = cast(Options, {
                'temperature': temperature,
                'num_predict': max_tokens,
                'top_p': self.config.get('model.top_p', 0.9),
                'repeat_penalty': self.config.get('model.repeat_penalty', 1.1)
            })

            response = self.client.chat(
                model=self.model_name,
                messages=[{'role': 'user', 'content': prompt}],
                stream=stream,
                options=typed_options 
            )
            
            if stream:
                return response
            else:
                return response['message']['content']
                
        except Exception as e:
            return f"❌ Error generating response: {e}"

    def generate_with_context(self, prompt: str, context: str,
                             temperature: Optional[float] = None,
                             max_tokens: Optional[int] = None) -> str:
        """Generate a response with provided context."""
        context_prompt = f"""Context: {context}

Question: {prompt}

Answer based on the context provided:"""
        
        return self.generate(context_prompt, temperature, max_tokens)