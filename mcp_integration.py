#!/usr/bin/env python3
"""
MCP Integration for the Llama RAG System

This module integrates Model Context Protocol tools with the main chat interface.
"""

from typing import Dict, List, Any, Optional
import json
from homicide_mcp import HomicideDataMCP, create_homicide_tools
from pathlib import Path

class MCPIntegration:
    """Integration layer for MCP tools in the Llama RAG system."""
    
    def __init__(self):
        self.homicide_data = None
        self.available_tools = []
        self.initialize_mcp_tools()
    
    def initialize_mcp_tools(self):
        """Initialize MCP tools and data sources."""
        try:
            # Initialize homicide data
            csv_path = Path("./knowledge_base/Homicides_2001_to_present.csv")
            if csv_path.exists():
                self.homicide_data = HomicideDataMCP(str(csv_path))
                self.available_tools = create_homicide_tools()
                print(f"✅ MCP initialized with {len(self.available_tools)} homicide data tools")
            else:
                print(f"⚠️ Homicide CSV not found at {csv_path}")
                
        except Exception as e:
            print(f"❌ Error initializing MCP tools: {e}")
    
    def get_available_tools(self) -> List[Dict[str, str]]:
        """Get list of available MCP tools."""
        if not self.available_tools:
            return []
        
        tools_info = []
        for tool in self.available_tools:
            tools_info.append({
                'name': tool.name,
                'description': tool.description,
                'usage': f"Use /mcp {tool.name} to call this tool"
            })
        
        return tools_info
    
    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call an MCP tool with the given arguments."""
        if not self.homicide_data:
            return {"error": "MCP tools not initialized"}
        
        # Validate tool exists
        tool_names = [tool.name for tool in self.available_tools]
        if tool_name not in tool_names:
            return {"error": f"Tool '{tool_name}' not found. Available tools: {', '.join(tool_names)}"}
        
        try:
            # Call the appropriate method directly on the homicide_data instance
            if tool_name == "query_homicides_advanced":
                result = self.homicide_data.query_homicides_advanced(
                    start_year=arguments.get("start_year"),
                    end_year=arguments.get("end_year"),
                    ward=arguments.get("ward"),
                    district=arguments.get("district"),
                    community_area=arguments.get("community_area"),
                    arrest_status=arguments.get("arrest_status"),
                    domestic=arguments.get("domestic"),
                    location_type=arguments.get("location_type"),
                    group_by=arguments.get("group_by"),
                    top_n=arguments.get("top_n", 10),
                    limit=arguments.get("limit", 100)
                )
                
            elif tool_name == "get_iucr_info":
                iucr_code = arguments.get("iucr_code")
                result = self.homicide_data.get_iucr_info(iucr_code)
                
            else:
                result = {"error": f"Unknown tool: {tool_name}"}
            
            return result
        except Exception as e:
            return {"error": f"Error calling tool '{tool_name}': {str(e)}"}
    
    def parse_mcp_command(self, command_text: str) -> tuple[Optional[str], Optional[Dict[str, Any]]]:
        """Parse an MCP command from user input."""
        try:
            parts = command_text.strip().split(' ', 1)
            if len(parts) < 1:
                return None, None
            
            tool_name = parts[0]
            
            # Parse arguments (simple key=value format or JSON)
            arguments = {}
            if len(parts) > 1:
                args_text = parts[1].strip()
                
                # Try to parse as JSON first
                try:
                    arguments = json.loads(args_text)
                except json.JSONDecodeError:
                    # Parse as simple key=value pairs
                    if '=' in args_text:
                        for pair in args_text.split():
                            if '=' in pair:
                                key, value = pair.split('=', 1)
                                # Try to convert to appropriate type
                                try:
                                    # Try integer
                                    if value.isdigit():
                                        arguments[key] = int(value)
                                    # Try boolean
                                    elif value.lower() in ('true', 'false'):
                                        arguments[key] = value.lower() == 'true'
                                    else:
                                        arguments[key] = value
                                except:
                                    arguments[key] = value
                    else:
                        # Single argument, assume it's for the first parameter
                        if tool_name == "get_iucr_info":
                            arguments["iucr_code"] = args_text
                        elif tool_name == "query_homicides_advanced":
                            # For advanced queries, try to parse simple patterns
                            if args_text.isdigit():
                                # Could be year or ward - assume year for single number
                                arguments["start_year"] = int(args_text)
                                arguments["end_year"] = int(args_text)
                            else:
                                # Could be location type or other string parameter
                                arguments["location_type"] = args_text
            
            return tool_name, arguments
            
        except Exception as e:
            return None, {"error": f"Error parsing command: {str(e)}"}
    
    def format_tool_result(self, result: Dict[str, Any]) -> str:
        """Format MCP tool result for display."""
        if "error" in result:
            return f"❌ Error: {result['error']}"
        
        try:
            # Format specific tool results
            if "total_matches" in result and "filters_applied" in result:
                # Advanced query result
                response = f"🔍 **Advanced Homicide Query Results**\n"
                
                if result['filters_applied']:
                    response += f"**Filters Applied:** {', '.join(result['filters_applied'])}\n\n"
                
                response += f"**Summary:**\n"
                response += f"  Total matches: {result['total_matches']}\n"
                response += f"  Arrests made: {result['arrest_count']} ({result['arrest_rate']})\n"
                response += f"  Domestic cases: {result['domestic_count']} ({result['domestic_rate']})\n\n"
                
                # Handle primary_breakdown for focused results
                if result.get('primary_breakdown') and result['primary_breakdown'].get('data'):
                    breakdown = result['primary_breakdown']
                    breakdown_type = breakdown['type'].replace('_', ' ').title()
                    response += f"**{breakdown_type} Breakdown (Ranked by Count):**\n"
                    
                    sorted_items = sorted(breakdown['data'].items(), key=lambda x: x[1], reverse=True)
                    for item, count in sorted_items:
                        if breakdown['type'] == 'location':
                            response += f"  {item}: {count} homicides\n"
                        else:
                            response += f"  {breakdown_type} {item}: {count} homicides\n"
                    response += "\n"
                    
                    # For group_by queries, highlight the top result
                    if sorted_items:
                        top_item, top_count = sorted_items[0]
                        response += f"**Answer: {breakdown_type} {top_item} had the most with {top_count} homicides.**\n\n"
                
                # Show detailed breakdowns only if no primary_breakdown (i.e., no group_by used)
                if not result.get('primary_breakdown') or not result['primary_breakdown'].get('data'):
                    if result['year_breakdown']:
                        response += f"**Year Breakdown:**\n"
                        for year, count in sorted(result['year_breakdown'].items()):
                            response += f"  {year}: {count} homicides\n"
                        response += "\n"
                    
                    if result.get('ward_breakdown'):
                        breakdown_size = len(result['ward_breakdown'])
                        response += f"**Ward Breakdown (Top {breakdown_size}):**\n"
                        sorted_wards = sorted(result['ward_breakdown'].items(), key=lambda x: x[1], reverse=True)
                        for ward, count in sorted_wards:
                            response += f"  Ward {ward}: {count} homicides\n"
                        response += "\n"
                    
                    if result.get('district_breakdown'):
                        breakdown_size = len(result['district_breakdown'])
                        response += f"**District Breakdown (Top {breakdown_size}):**\n"
                        sorted_districts = sorted(result['district_breakdown'].items(), key=lambda x: x[1], reverse=True)
                        for district, count in sorted_districts:
                            response += f"  District {district}: {count} homicides\n"
                        response += "\n"
                    
                    if result.get('community_area_breakdown'):
                        breakdown_size = len(result['community_area_breakdown'])
                        response += f"**Community Area Breakdown (Top {breakdown_size}):**\n"
                        sorted_cas = sorted(result['community_area_breakdown'].items(), key=lambda x: x[1], reverse=True)
                        for ca, count in sorted_cas:
                            response += f"  Community Area {ca}: {count} homicides\n"
                        response += "\n"
                
                if result.get('top_locations'):
                    response += f"**Top Locations:**\n"
                    for location, count in list(result['top_locations'].items())[:3]:
                        response += f"  {location}: {count} cases\n"
                    response += "\n"
                
                if result['sample_records']:
                    response += f"**Sample Records ({len(result['sample_records'])}):**\n"
                    for i, record in enumerate(result['sample_records'][:3], 1):
                        response += f"{i}. **Case {record['case_number']}** ({record['year']})\n"
                        response += f"   Ward: {record['ward']}, District: {record['district']}\n"
                        response += f"   Location: {record['block']}\n"
                        response += f"   Arrest: {'Yes' if record['arrest'] else 'No'}\n\n"
                
                return response
                
            elif "year" in result and "records" in result:
                # Year query result
                response = f"📅 **Homicides in {result['year']}**\n"
                response += f"Total records: {result['total_records']}\n"
                response += f"Showing: {result['returned_records']} records\n\n"
                
                for i, record in enumerate(result['records'][:5], 1):  # Show first 5
                    response += f"{i}. **Case {record['case_number']}**\n"
                    response += f"   Date: {record['date']}\n"
                    response += f"   Location: {record['block']}\n"
                    response += f"   Description: {record['description']}\n"
                    response += f"   Arrest: {'Yes' if record['arrest'] else 'No'}\n\n"
                
                if result['returned_records'] > 5:
                    response += f"... and {result['returned_records'] - 5} more records\n"
                
                return response
            
            elif "total_homicides" in result:
                # Statistics result
                response = f"📊 **Homicide Statistics**\n"
                response += f"Total homicides: {result['total_homicides']}\n"
                response += f"Year range: {result['year_range']}\n"
                response += f"Arrests made: {result['arrests_made']} ({result['arrest_rate']})\n"
                response += f"Domestic cases: {result['domestic_cases']} ({result['domestic_rate']})\n\n"
                
                if 'top_districts' in result:
                    response += "**Top Districts:**\n"
                    for district, count in list(result['top_districts'].items())[:3]:
                        response += f"  District {district}: {count} cases\n"
                
                return response
            
            elif "query" in result and "records" in result:
                # Location search result
                response = f"🔍 **Location Search: '{result['query']}'**\n"
                response += f"Total matches: {result['total_matches']}\n"
                response += f"Showing: {result['returned_records']} records\n\n"
                
                for i, record in enumerate(result['records'][:3], 1):  # Show first 3
                    response += f"{i}. **Case {record['case_number']}** ({record['year']})\n"
                    response += f"   Location: {record['block']}\n"
                    response += f"   Type: {record['location_description']}\n"
                    response += f"   Arrest: {'Yes' if record['arrest'] else 'No'}\n\n"
                
                return response
            
            elif "iucr_code" in result:
                # IUCR specific result
                response = f"📋 **IUCR Code: {result['iucr_code']}**\n"
                response += f"Type: {result['primary_type']}\n"
                response += f"Description: {result['description']}\n"
                response += f"Total cases: {result['total_cases']}\n\n"
                response += result['explanation']
                return response
            
            elif "explanation" in result and "unique_codes_count" in result:
                # IUCR overview result
                response = f"📋 **IUCR System Overview**\n"
                response += f"{result['explanation']}\n\n"
                response += f"Unique codes in dataset: {result['unique_codes_count']}\n"
                if 'sample_codes' in result:
                    response += f"Most common codes: {', '.join(result['sample_codes'])}\n"
                return response
            
            else:
                # Generic JSON formatting
                return f"📋 **Result:**\n```json\n{json.dumps(result, indent=2)}\n```"
                
        except Exception as e:
            return f"📋 **Raw Result:** {json.dumps(result, indent=2)}\n\n⚠️ Format error: {str(e)}"

# Create global instance
mcp_integration = MCPIntegration()
