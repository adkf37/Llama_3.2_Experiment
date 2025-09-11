import ollama
from ollama._types import Options
from typing import List, Dict, Any, Optional, Union, cast
from config import config
import json

class LlamaClient:
    """Client for interacting with Llama models via Ollama."""
    
    def __init__(self, model_name: Optional[str] = None):
        self.config = config
        self.model_name = model_name or self.config.get('model.name', 'llama3.2:3b')
        self.client = ollama.Client()
        
        # Check if model is available
        if not self._check_model_availability():
            print(f"⚠️  Model {self.model_name} not found. Please pull it with: ollama pull {self.model_name}")

    def _check_model_availability(self) -> bool:
        """Check if the specified model is available locally."""
        try:
            models = self.client.list()
            available_models = [model['name'] for model in models['models']]
            
            if self.model_name not in available_models:
                print(f"⚠️  Model {self.model_name} not found. Available models:")
                for model in available_models:
                    print(f"  📦 {model}")
                print(f"To download the model, run: ollama pull {self.model_name}")
                return False
            return True
        except Exception as e:
            print(f"❌ Error checking model availability: {e}")
            return False

    def generate_with_tools(self, prompt: str, tools: List[Dict[str, Any]], 
                          temperature: Optional[float] = None,
                          max_tokens: Optional[int] = None) -> Dict[str, Any]:
        """Generate response with tool calling capability."""
        temperature = temperature or self.config.get('model.temperature', 0.7)
        max_tokens = max_tokens or self.config.get('model.max_tokens', 2048)
        
        # Create system prompt that explains available tools
        tools_desc = []
        for tool in tools:
            params = tool.get("parameters", {})
            required = tool.get("required", [])
            param_desc = ", ".join([f"{k}: {v.get('description', k)}" for k, v in params.items()])
            tools_desc.append(f"- {tool['name']}({param_desc}): {tool['description']}")

        system_prompt = f"""You are an assistant that can use tools to answer questions about homicide data. 

Available tools:
{chr(10).join(tools_desc)}

When you need data to answer a question, respond with a tool call in this exact format:
TOOL_CALL: {{"name": "tool_name", "arguments": {{"arg": "value"}}}}

Examples:
- "How many homicides in 2023?" → TOOL_CALL: {{"name": "query_homicides_advanced", "arguments": {{"start_year": 2023, "end_year": 2023}}}}
- "What are the overall statistics?" → TOOL_CALL: {{"name": "query_homicides_advanced", "arguments": {{}}}}
- "Which ward had the most homicides in 2013?" → TOOL_CALL: {{"name": "query_homicides_advanced", "arguments": {{"start_year": 2013, "end_year": 2013, "group_by": "ward"}}}}
- "What district had the most homicides from 2020-2022?" → TOOL_CALL: {{"name": "query_homicides_advanced", "arguments": {{"start_year": 2020, "end_year": 2022, "group_by": "district"}}}}
- "Show top 5 community areas with homicides" → TOOL_CALL: {{"name": "query_homicides_advanced", "arguments": {{"group_by": "community_area", "top_n": 5}}}}
- "Find domestic violence homicides on streets" → TOOL_CALL: {{"name": "query_homicides_advanced", "arguments": {{"domestic": true, "location_type": "STREET"}}}}
- "What does IUCR mean?" → TOOL_CALL: {{"name": "get_iucr_info", "arguments": {{}}}}

Use query_homicides_advanced for ALL data analysis. Use get_iucr_info ONLY for IUCR code explanations.

IMPORTANT: For "which X had the most" or "top X" questions, ALWAYS use group_by parameter:
- "which ward" → group_by: "ward"
- "which district" → group_by: "district"  
- "which community area" → group_by: "community_area"
- "which location" → group_by: "location"
If you don't need tools, just answer normally."""

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