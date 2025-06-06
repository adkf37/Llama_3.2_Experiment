import ollama
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
            if hasattr(models_response, 'models') and models_response.models:
                available_models = [model.model for model in models_response.models]
            elif isinstance(models_response, dict) and 'models' in models_response:
                available_models = [m.get('name', m.get('model', '')) for m in models_response['models']]
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
            if hasattr(models_response, 'models') and models_response.models:
                models = [str(model.model) for model in models_response.models if model.model]
            elif isinstance(models_response, dict) and 'models' in models_response:
                models = [str(m.get('name', m.get('model', ''))) for m in models_response['models'] if m.get('name') or m.get('model')]
            else:
                models = []
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
        options: Dict[str, Any] = {}
        if temperature is not None:
            options['temperature'] = temperature
        else:
            options['temperature'] = self.config.get('model.temperature', 0.7)
        if max_tokens is not None:
            options['num_predict'] = max_tokens
        else:
            options['num_predict'] = self.config.get('model.max_tokens', 2048)
        
        try:
            response = self.client.chat(
                model=self.model_name,
                messages=[{'role': 'user', 'content': prompt}],
                options=options,
                stream=stream
            )
            if stream:
                return response
            # Simplified non-stream response handling
            if isinstance(response, dict):
                if 'message' in response and isinstance(response['message'], dict) and 'content' in response['message']:
                    return response['message']['content']
                if 'response' in response:
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
        enhanced_prompt = (f"""Context Information:\n{context_text}\n\nQuestion: {prompt}\n
Please answer based on the context. If irrelevant, provide a general answer.""")
        response = self.generate(
            prompt=enhanced_prompt,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response if isinstance(response, str) else str(response)

    def get_model_info(self) -> Dict[str, Any]:
        return {'model_name': self.model_name, 'available': self._check_model_availability()}

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