import os
from typing import List, Dict, Any, Optional, Union

import google.generativeai as genai

from config import config
from prompt_registry import build_tool_system_prompt


class LlamaClient:
    """Client for interacting with Gemini models via the Google Generative AI API."""

    def __init__(self, model_name: Optional[str] = None):
        self.config = config
        self.model_name = model_name or self.config.get('model.name', 'gemini-1.5-pro-latest')
        self.system_prompt_variant = self.config.get('prompts.system_prompt_variant', 'tool_use_v1')

        api_key_env = self.config.get('model.api_key_env', 'GOOGLE_API_KEY')
        api_key = os.getenv(api_key_env)

        if not api_key:
            raise EnvironmentError(
                f"Missing Gemini API key. Set the '{api_key_env}' environment variable."
            )

        genai.configure(api_key=api_key)
        self.client = genai.GenerativeModel(self.model_name)

    def generate_with_tools(self, prompt: str, tools: List[Dict[str, Any]],
                            temperature: Optional[float] = None,
                            max_tokens: Optional[int] = None) -> Dict[str, Any]:
        """Generate response with tool calling capability."""
        temperature = temperature or self.config.get('model.temperature', 0.7)
        max_tokens = max_tokens or self.config.get('model.max_tokens', 2048)

        system_prompt = build_tool_system_prompt(self.system_prompt_variant, tools)
        composed_prompt = f"{system_prompt}\n\nUser question: {prompt}"

        try:
            generation_config = {
                'temperature': temperature,
                'max_output_tokens': max_tokens,
                'top_p': self.config.get('model.top_p', 0.9)
            }

            response = self.client.generate_content(
                composed_prompt,
                generation_config=generation_config
            )

            text = getattr(response, 'text', '') or ''
            return {
                "content": text,
                "needs_tool_call": "TOOL_CALL:" in text
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
            generation_config = {
                'temperature': temperature,
                'max_output_tokens': max_tokens,
                'top_p': self.config.get('model.top_p', 0.9)
            }

            if stream:
                return self.client.generate_content(
                    prompt,
                    generation_config=generation_config,
                    stream=True
                )

            response = self.client.generate_content(
                prompt,
                generation_config=generation_config
            )

            return getattr(response, 'text', str(response))

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
