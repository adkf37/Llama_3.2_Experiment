import ollama
from ollama._types import Options  # Import the Options type
from typing import List, Dict, Any, Optional, Union
from config import config

class LlamaClient:
    """Client for interacting with Llama models via Ollama."""
    
    def __init__(self, model_name: Optional[str] = None):
        self.config = config
        self.model_name = model_name or self.config.get('model.name', 'llama3.2:3b')
        self.client = ollama.Client()
        
        # Check if model is available
        if not self._check_model_availability():
            print(f"⚠️  Model {self.model_name} not found. Available models:")
            self.list_models()
            print(f"To download the model, run: ollama pull {self.model_name}")

    def _check_model_availability(self) -> bool:
        """Check if the specified model is available locally."""
        try:
            models_response = self.client.list()
            # Handle different response formats from ollama client
            if isinstance(models_response, dict) and 'models' in models_response:
                available_models = [str(m.get('name', m.get('model', ''))) for m in models_response['models'] if isinstance(m, dict)]
            else:
                available_models = []
            return self.model_name in available_models
        except Exception as e:
            print(f"Error checking model availability: {e}")
            return False

    def list_models(self) -> List[str]:
        """List all available models."""
        try:
            models_response = self.client.list()
            models = []
            
            # Handle dict response format
            if isinstance(models_response, dict) and 'models' in models_response:
                models = [str(m.get('name', m.get('model', ''))) for m in models_response['models'] if m.get('name') or m.get('model')]
            
            for model in models:
                print(f"  📦 {model}")
            return models
        except Exception as e:
            print(f"Error listing models: {e}")
            return []

    def generate(self, prompt: str,
                 temperature: Optional[float] = None,
                 max_tokens: Optional[int] = None,
                 stream: bool = False) -> Union[str, Any]:
        """Generate text using the Llama model."""
        # Prepare model parameters
        current_options: Dict[str, Any] = {}
        if temperature is not None:
            current_options['temperature'] = temperature
        else:
            current_options['temperature'] = self.config.get('model.temperature', 0.7)
        if max_tokens is not None:
            current_options['num_predict'] = max_tokens
        else:
            current_options['num_predict'] = self.config.get('model.max_tokens', 2048)
        
        # Cast to ollama Options type
        typed_options: Options = current_options # type: ignore

        try:
            if stream:
                response = self.client.generate(
                    model=self.model_name,
                    prompt=prompt,
                    stream=True,
                    options=typed_options
                )
                return response
            else:
                response = self.client.generate(
                    model=self.model_name,
                    prompt=prompt,
                    stream=False,
                    options=typed_options
                )
                
            # Handle response
            if isinstance(response, dict) and 'response' in response:
                return response['response']
            return str(response)
        except Exception as e:
            print(f"Error generating response: {e}")
            return f"Error: {e}"

    def generate_with_context(self, prompt: str,
                              context: List[str],
                              temperature: Optional[float] = None,
                              max_tokens: Optional[int] = None) -> str:
        """Generate text with additional context from RAG system."""
        context_text = "\n\n".join([f"Context {i+1}: {ctx}" for i, ctx in enumerate(context)])
        enhanced_prompt = f"""Context Information:
{context_text}

Question: {prompt}

Please answer based on the context provided. If the context is not relevant, provide a general answer."""
        
        response = self.generate(
            prompt=enhanced_prompt,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response if isinstance(response, str) else str(response)

    def get_model_info(self) -> Dict[str, Any]:
        """Get model information."""
        return {
            'model_name': self.model_name, 
            'available': self._check_model_availability()
        }

    def pull_model(self, model_name: str) -> bool:
        """Pull a model from Ollama registry."""
        try:
            print(f"Pulling model: {model_name}")
            self.client.pull(model_name)
            print(f"✅ Successfully pulled {model_name}")
            return True
        except Exception as e:
            print(f"❌ Failed to pull {model_name}: {e}")
            return False