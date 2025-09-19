import json
import re
import time
from typing import Dict, Any, Optional, Union
import mcp_integration

class IntelligentMCPHandler:
    """Handles intelligent MCP tool calling based on natural language questions."""
    
    def __init__(self):
        self.tools = [
            {
                "name": "query_homicides_advanced",
                "description": "Query homicide data with flexible filtering options. Use this for ALL data analysis queries including: single years, year ranges, geographic filters, location searches, arrest status, domestic cases, and overall statistics. Examples: 'homicides in 2023', 'overall statistics', 'homicides from 2015-2019 in ward 3', 'street homicides with arrests'.",
                "parameters": {
                    "start_year": {"type": "integer", "description": "Start year for date range filter (or single year if used alone)"},
                    "end_year": {"type": "integer", "description": "End year for date range filter"},
                    "ward": {"type": "integer", "description": "Ward number to filter by (1-50)"},
                    "district": {"type": "integer", "description": "Police district number to filter by"},
                    "community_area": {"type": "integer", "description": "Community area number to filter by"},
                    "arrest_status": {"type": "boolean", "description": "Filter by arrest status: true for arrests made, false for no arrests"},
                    "domestic": {"type": "boolean", "description": "Filter by domestic violence cases"},
                    "location_type": {"type": "string", "description": "Filter by location type (e.g., 'STREET', 'APARTMENT', 'RESIDENCE')"},
                    "group_by": {"type": "string", "description": "Focus results on specific grouping for 'which X had the most' queries: 'ward', 'district', 'community_area', or 'location'"},
                    "top_n": {"type": "integer", "description": "Number of items to show in breakdowns (default 10)"}
                },
                "required": []
            },
            {
                "name": "get_iucr_info",
                "description": "Get information and explanations about IUCR (Illinois Uniform Crime Reporting) codes. Use this ONLY when users ask about what IUCR means, what specific codes mean, or need educational information about crime classification codes.",
                "parameters": {
                    "iucr_code": {"type": "string", "description": "Specific IUCR code to look up (optional, e.g., '0110'). If not provided, returns overview of IUCR system."}
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
    
    def execute_tool_call(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool call and return structured execution details."""
        tool_name = tool_call.get("name")
        arguments = tool_call.get("arguments", {})

        execution_summary = {
            "tool_name": tool_name,
            "arguments": arguments,
            "raw_result": None,
            "formatted_result": None,
            "error": None
        }

        if not tool_name or tool_name not in [tool["name"] for tool in self.tools]:
            execution_summary["error"] = f"Unknown tool: {tool_name}"
            execution_summary["formatted_result"] = f"❌ Unknown tool: {tool_name}"
            return execution_summary

        try:
            mcp_instance = getattr(mcp_integration, "mcp_integration", None)
            if mcp_instance is None:
                mcp_instance = mcp_integration.MCPIntegration()
            result = mcp_instance.call_tool(str(tool_name), arguments)
            execution_summary["raw_result"] = result

            if isinstance(result, dict) and "error" in result:
                execution_summary["error"] = result["error"]
                execution_summary["formatted_result"] = f"❌ {result['error']}"
            else:
                execution_summary["formatted_result"] = mcp_instance.format_tool_result(result)

        except Exception as e:
            execution_summary["error"] = str(e)
            execution_summary["formatted_result"] = f"❌ Error executing tool {tool_name}: {e}"

        return execution_summary

    def handle_question_with_tools(
        self,
        question: str,
        llama_client,
        include_trace: bool = False
    ) -> Union[str, Dict[str, Any]]:
        """Handle a question that might require tool calling."""
        print("🔍 Generating response with tool calling capability...")

        # First, ask the LLM if it needs to use tools
        response = llama_client.generate_with_tools(question, self.tools)
        print(f"🤖 LLM Response: {response.get('content', 'No content')[:200]}...")
        print(f"🔧 Needs tool call: {response.get('needs_tool_call', False)}")

        interaction_trace: Dict[str, Any] = {
            "question": question,
            "initial_model_response": response,
            "needs_tool_call": response.get("needs_tool_call", False),
            "tool_call": None,
            "tool_execution": None,
            "final_answer": None
        }

        if not response.get("needs_tool_call", False):
            # No tool call needed, return the direct response
            print("ℹ️  No tool call needed, returning direct response")
            interaction_trace["final_answer"] = response["content"]
            return interaction_trace if include_trace else response["content"]

        # Parse and execute tool call
        print("🔍 Parsing tool call from response...")
        tool_call = self.parse_tool_call(response["content"])
        if not tool_call:
            error_msg = f"❌ Could not parse tool call from response: {response['content']}"
            print(error_msg)
            interaction_trace["final_answer"] = error_msg
            return interaction_trace if include_trace else error_msg

        print(f"🔧 Calling tool: {tool_call['name']} with args: {tool_call.get('arguments', {})}")
        interaction_trace["tool_call"] = tool_call

        # Execute the tool
        tool_start = time.perf_counter()
        tool_execution = self.execute_tool_call(tool_call)
        tool_execution["latency_seconds"] = time.perf_counter() - tool_start
        interaction_trace["tool_execution"] = tool_execution
        print(f"📊 Tool result (first 200 chars): {str(tool_execution.get('formatted_result', ''))[:200]}...")

        if tool_execution.get("error"):
            interaction_trace["final_answer"] = tool_execution.get("formatted_result")
            return interaction_trace if include_trace else tool_execution.get("formatted_result")

        # Now ask the LLM to formulate a final answer based on the tool result
        follow_up_prompt = f"""Based on this data about homicides:

{tool_execution['formatted_result']}

Please answer the original question: "{question}"

Provide a clear, informative answer based on the data."""

        print("🔍 Generating final response based on tool result...")
        final_response = llama_client.generate(follow_up_prompt)
        print("✅ Final response generated")
        interaction_trace["final_answer"] = final_response
        return interaction_trace if include_trace else final_response

# Global instance
intelligent_mcp = IntelligentMCPHandler()