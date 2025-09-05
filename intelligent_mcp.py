import json
import re
from typing import Dict, Any, Optional
import mcp_integration

class IntelligentMCPHandler:
    """Handles intelligent MCP tool calling based on natural language questions."""
    
    def __init__(self):
        self.tools = [
            {
                "name": "get_homicides_by_year",
                "description": "Get homicide records for a specific year",
                "parameters": {
                    "year": {"type": "integer", "description": "The year to get homicides for"}
                },
                "required": ["year"]
            },
            {
                "name": "get_homicide_statistics", 
                "description": "Get overall homicide statistics including totals, arrest rates, trends, and top locations",
                "parameters": {},
                "required": []
            },
            {
                "name": "search_by_location",
                "description": "Search for homicides by location (street name, area, etc.)",
                "parameters": {
                    "location_query": {"type": "string", "description": "Location to search for"}
                },
                "required": ["location_query"]
            },
            {
                "name": "get_iucr_info",
                "description": "Get information about IUCR crime codes",
                "parameters": {
                    "iucr_code": {"type": "string", "description": "IUCR code to get info for (optional)"}
                },
                "required": []
            }
        ]
    
    def get_tools(self) -> list:
        """Get available tools for the LLM."""
        return self.tools
    
    def parse_tool_call(self, response_content: str) -> Optional[Dict[str, Any]]:
        """Parse a tool call from the LLM response."""
        print(f"🔍 Looking for TOOL_CALL in response: {response_content[:100]}...")
        
        if "TOOL_CALL:" not in response_content:
            print("ℹ️  No TOOL_CALL found in response")
            return None
            
        try:
            # Find the TOOL_CALL: part
            tool_call_start = response_content.find("TOOL_CALL:")
            if tool_call_start == -1:
                print("❌ TOOL_CALL: not found")
                return None
                
            # Find the JSON part starting after "TOOL_CALL:"
            json_start = response_content.find("{", tool_call_start)
            if json_start == -1:
                print("❌ No opening brace found after TOOL_CALL:")
                return None
                
            # Find the matching closing brace using more robust approach
            brace_count = 0
            json_end = json_start
            in_quotes = False
            escape_next = False
            
            for i, char in enumerate(response_content[json_start:], json_start):
                if escape_next:
                    escape_next = False
                    continue
                    
                if char == '\\':
                    escape_next = True
                    continue
                    
                if char == '"' and not escape_next:
                    in_quotes = not in_quotes
                    continue
                
                if not in_quotes:
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            json_end = i + 1
                            break
            
            # Extract and parse the JSON
            tool_call_json = response_content[json_start:json_end].strip()
            print(f"🔍 Extracted JSON: {tool_call_json}")
            
            # Try to fix common JSON issues
            if not tool_call_json.endswith('}'):
                tool_call_json += '}'
            
            tool_call = json.loads(tool_call_json)
            
            if "name" not in tool_call:
                print("❌ Tool call missing 'name' field")
                return None
                
            # Ensure arguments field exists
            if "arguments" not in tool_call:
                tool_call["arguments"] = {}
                
            print(f"✅ Successfully parsed tool call: {tool_call}")
            return tool_call
        except (json.JSONDecodeError, AttributeError) as e:
            print(f"❌ Error parsing tool call: {e}")
            print(f"❌ Raw response content: {response_content}")
            
            # Try a simpler extraction as fallback
            try:
                # Look for simple patterns like {"name": "tool_name"}
                import re
                pattern = r'TOOL_CALL:\s*(\{[^}]*\})'
                match = re.search(pattern, response_content)
                if match:
                    simple_json = match.group(1)
                    print(f"🔧 Trying fallback parsing: {simple_json}")
                    tool_call = json.loads(simple_json)
                    if "arguments" not in tool_call:
                        tool_call["arguments"] = {}
                    return tool_call
            except:
                pass
                
            return None
    
    def execute_tool_call(self, tool_call: Dict[str, Any]) -> str:
        """Execute a tool call and return the result."""
        tool_name = tool_call.get("name")
        arguments = tool_call.get("arguments", {})
        
        if not tool_name or tool_name not in [tool["name"] for tool in self.tools]:
            return f"❌ Unknown tool: {tool_name}"
        
        try:
            from mcp_integration import MCPIntegration
            mcp = MCPIntegration()
            result = mcp.call_tool(str(tool_name), arguments)
            
            # Format the result for display
            if isinstance(result, dict) and "error" in result:
                return f"❌ {result['error']}"
            else:
                return mcp.format_tool_result(result)
        except Exception as e:
            return f"❌ Error executing tool {tool_name}: {e}"
    
    def handle_question_with_tools(self, question: str, llama_client) -> str:
        """Handle a question that might require tool calling."""
        print("🔍 Generating response with tool calling capability...")
        
        # First, ask the LLM if it needs to use tools
        response = llama_client.generate_with_tools(question, self.tools)
        print(f"🤖 LLM Response: {response.get('content', 'No content')[:200]}...")
        print(f"🔧 Needs tool call: {response.get('needs_tool_call', False)}")
        
        if not response.get("needs_tool_call", False):
            # No tool call needed, return the direct response
            print("ℹ️  No tool call needed, returning direct response")
            return response["content"]
        
        # Parse and execute tool call
        print("🔍 Parsing tool call from response...")
        tool_call = self.parse_tool_call(response["content"])
        if not tool_call:
            error_msg = f"❌ Could not parse tool call from response: {response['content']}"
            print(error_msg)
            return error_msg
        
        print(f"🔧 Calling tool: {tool_call['name']} with args: {tool_call.get('arguments', {})}")
        
        # Execute the tool
        tool_result = self.execute_tool_call(tool_call)
        print(f"📊 Tool result (first 200 chars): {str(tool_result)[:200]}...")
        
        # Now ask the LLM to formulate a final answer based on the tool result
        follow_up_prompt = f"""Based on this data about homicides:

{tool_result}

Please answer the original question: "{question}"

Provide a clear, informative answer based on the data."""

        print("🔍 Generating final response based on tool result...")
        final_response = llama_client.generate(follow_up_prompt)
        print("✅ Final response generated")
        return final_response

# Global instance
intelligent_mcp = IntelligentMCPHandler()