#!/usr/bin/env python3
"""
MCP Server for Chicago Homicide Data

This server provides tools to query and analyze the Chicago homicide dataset.
"""

import asyncio
import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional
import sys
import argparse

# Import MCP types
import mcp
from mcp import Tool

class HomicideDataMCP:
    """MCP Server for Chicago Homicide Data Analysis."""
    
    def __init__(self, csv_path: str):
        self.csv_path = Path(csv_path)
        self.df = None
        self.load_data()
        
    def load_data(self):
        """Load the homicide CSV data."""
        try:
            self.df = pd.read_csv(self.csv_path)
            
            # Clean and standardize data
            # Specify date format to avoid parsing warning: MM/dd/yyyy HH:mm:ss AM/PM
            self.df['Date'] = pd.to_datetime(self.df['Date'], format='%m/%d/%Y %I:%M:%S %p', errors='coerce')
            self.df['Year'] = pd.to_numeric(self.df['Year'], errors='coerce')
            self.df['Arrest'] = self.df['Arrest'].astype(str).str.lower().isin(['true', '1', 'yes'])
            self.df['Domestic'] = self.df['Domestic'].astype(str).str.lower().isin(['true', '1', 'yes'])
            
            print(f"✅ Loaded {len(self.df)} homicide records from {self.csv_path}")
            
        except Exception as e:
            print(f"❌ Error loading homicide data: {e}")
            raise

    def get_records_by_year(self, year: int, limit: int = 100) -> Dict[str, Any]:
        """Get homicide records for a specific year."""
        try:
            filtered_df = self.df[self.df['Year'] == year].head(limit)
            
            records = []
            for _, row in filtered_df.iterrows():
                records.append({
                    'id': str(row.get('ID', '')),
                    'case_number': str(row.get('Case Number', '')),
                    'date': str(row.get('Date', '')),
                    'block': str(row.get('Block', '')),
                    'iucr': str(row.get('IUCR', '')),
                    'description': str(row.get('Description', '')),
                    'location_description': str(row.get('Location Description', '')),
                    'arrest': bool(row.get('Arrest', False)),
                    'domestic': bool(row.get('Domestic', False)),
                    'district': str(row.get('District', '')),
                    'ward': str(row.get('Ward', '')),
                    'community_area': str(row.get('Community Area', ''))
                })
            
            return {
                'year': year,
                'total_records': int(len(self.df[self.df['Year'] == year])),
                'returned_records': len(records),
                'records': records
            }
            
        except Exception as e:
            return {'error': f"Error querying year {year}: {str(e)}"}

    def get_statistics(self, start_year: Optional[int] = None, end_year: Optional[int] = None) -> Dict[str, Any]:
        """Get statistics about homicides."""
        try:
            df = self.df.copy()
            
            # Filter by year range if provided
            if start_year:
                df = df[df['Year'] >= start_year]
            if end_year:
                df = df[df['Year'] <= end_year]
            
            # Convert to regular Python types for JSON serialization
            by_year = {str(int(k)): int(v) for k, v in df.groupby('Year').size().to_dict().items() if pd.notna(k)}
            top_districts = {str(k): int(v) for k, v in df['District'].value_counts().head(5).to_dict().items() if pd.notna(k)}
            top_wards = {str(k): int(v) for k, v in df['Ward'].value_counts().head(5).to_dict().items() if pd.notna(k)}
            top_community_areas = {str(k): int(v) for k, v in df['Community Area'].value_counts().head(5).to_dict().items() if pd.notna(k)}
            
            stats = {
                'total_homicides': int(len(df)),
                'year_range': f"{int(df['Year'].min())} - {int(df['Year'].max())}",
                'arrests_made': int(df['Arrest'].sum()),
                'arrest_rate': f"{(df['Arrest'].sum() / len(df) * 100):.1f}%",
                'domestic_cases': int(df['Domestic'].sum()),
                'domestic_rate': f"{(df['Domestic'].sum() / len(df) * 100):.1f}%",
                'by_year': by_year,
                'top_districts': top_districts,
                'top_wards': top_wards,
                'top_community_areas': top_community_areas
            }
            
            return stats
            
        except Exception as e:
            return {'error': f"Error generating statistics: {str(e)}"}

    def search_by_location(self, location_query: str, limit: int = 50) -> Dict[str, Any]:
        """Search homicides by location."""
        try:
            df = self.df.copy()
            
            # Search in multiple location fields
            mask = (
                df['Block'].str.contains(location_query, case=False, na=False) |
                df['Location Description'].str.contains(location_query, case=False, na=False)
            )
            
            filtered_df = df[mask].head(limit)
            
            records = []
            for _, row in filtered_df.iterrows():
                records.append({
                    'id': str(row.get('ID', '')),
                    'case_number': str(row.get('Case Number', '')),
                    'date': str(row.get('Date', '')),
                    'year': str(row.get('Year', '')),
                    'block': str(row.get('Block', '')),
                    'location_description': str(row.get('Location Description', '')),
                    'arrest': bool(row.get('Arrest', False)),
                    'domestic': bool(row.get('Domestic', False))
                })
            
            return {
                'query': location_query,
                'total_matches': int(mask.sum()),
                'returned_records': len(records),
                'records': records
            }
            
        except Exception as e:
            return {'error': f"Error searching location '{location_query}': {str(e)}"}

    def get_iucr_info(self, iucr_code: Optional[str] = None) -> Dict[str, Any]:
        """Get information about IUCR codes."""
        try:
            if iucr_code:
                # Get specific IUCR code info
                iucr_df = self.df[self.df['IUCR'] == iucr_code]
                if iucr_df.empty:
                    return {'error': f"IUCR code '{iucr_code}' not found"}
                
                sample_row = iucr_df.iloc[0]
                return {
                    'iucr_code': iucr_code,
                    'primary_type': str(sample_row.get('Primary Type', '')),
                    'description': str(sample_row.get('Description', '')),
                    'total_cases': int(len(iucr_df)),
                    'explanation': "IUCR stands for Illinois Uniform Crime Reporting. It's a standardized system used by law enforcement agencies in Illinois to classify and report crimes."
                }
            else:
                # Get summary of IUCR codes
                return {
                    'explanation': "IUCR stands for Illinois Uniform Crime Reporting. It's a standardized system used by law enforcement agencies in Illinois to classify and report crimes.",
                    'most_common_code': str(self.df['IUCR'].mode().iloc[0] if not self.df['IUCR'].mode().empty else 'Unknown'),
                    'unique_codes_count': int(self.df['IUCR'].nunique()),
                    'sample_codes': list(self.df['IUCR'].value_counts().head(5).index.astype(str))
                }
                
        except Exception as e:
            return {'error': f"Error getting IUCR information: {str(e)}"}

def create_homicide_tools() -> List[Tool]:
    """Create the MCP tools for homicide data analysis."""
    return [
        Tool(
            name="get_homicides_by_year",
            description="Get homicide records for a specific year. Returns detailed information about homicides that occurred in the specified year.",
            inputSchema={
                "type": "object",
                "properties": {
                    "year": {
                        "type": "integer", 
                        "description": "Year to query (e.g., 2023, 2022, 2021, etc.)",
                        "minimum": 2001,
                        "maximum": 2024
                    },
                    "limit": {
                        "type": "integer", 
                        "description": "Maximum number of records to return (default: 100)",
                        "default": 100,
                        "minimum": 1,
                        "maximum": 1000
                    }
                },
                "required": ["year"]
            }
        ),
        Tool(
            name="get_homicide_statistics",
            description="Get comprehensive statistical analysis of homicide data including trends, arrest rates, and geographical distribution.",
            inputSchema={
                "type": "object",
                "properties": {
                    "start_year": {
                        "type": "integer", 
                        "description": "Start year for analysis (optional)",
                        "minimum": 2001,
                        "maximum": 2024
                    },
                    "end_year": {
                        "type": "integer", 
                        "description": "End year for analysis (optional)",
                        "minimum": 2001,
                        "maximum": 2024
                    }
                }
            }
        ),
        Tool(
            name="search_by_location",
            description="Search homicides by location including street names, neighborhoods, or location types (e.g., 'STREET', 'APARTMENT', 'KEDZIE').",
            inputSchema={
                "type": "object",
                "properties": {
                    "location_query": {
                        "type": "string", 
                        "description": "Location to search for. Can be a street name (e.g., 'KEDZIE'), location type (e.g., 'STREET', 'APARTMENT'), or any location-related keyword."
                    },
                    "limit": {
                        "type": "integer", 
                        "description": "Maximum number of records to return (default: 50)",
                        "default": 50,
                        "minimum": 1,
                        "maximum": 500
                    }
                },
                "required": ["location_query"]
            }
        ),
        Tool(
            name="get_iucr_info",
            description="Get information about IUCR (Illinois Uniform Crime Reporting) codes. IUCR codes classify different types of crimes in Illinois.",
            inputSchema={
                "type": "object",
                "properties": {
                    "iucr_code": {
                        "type": "string", 
                        "description": "Specific IUCR code to look up (optional, e.g., '0110'). If not provided, returns overview of IUCR system."
                    }
                }
            }
        )
    ]

# Global instance
homicide_data = None

def handle_tool_call(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Handle tool calls and return results."""
    global homicide_data
    
    if homicide_data is None:
        return {"error": "Homicide data not loaded"}
    
    try:
        if tool_name == "get_homicides_by_year":
            year = arguments.get("year")
            limit = arguments.get("limit", 100)
            return homicide_data.get_records_by_year(year, limit)
            
        elif tool_name == "get_homicide_statistics":
            start_year = arguments.get("start_year")
            end_year = arguments.get("end_year")
            return homicide_data.get_statistics(start_year, end_year)
            
        elif tool_name == "search_by_location":
            location_query = arguments.get("location_query")
            limit = arguments.get("limit", 50)
            return homicide_data.search_by_location(location_query, limit)
            
        elif tool_name == "get_iucr_info":
            iucr_code = arguments.get("iucr_code")
            return homicide_data.get_iucr_info(iucr_code)
            
        else:
            return {"error": f"Unknown tool: {tool_name}"}
            
    except Exception as e:
        return {"error": f"Error executing {tool_name}: {str(e)}"}

def main():
    """Main entry point for testing the homicide data MCP."""
    global homicide_data
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Chicago Homicide Data MCP Server")
    parser.add_argument(
        "--csv-path", 
        default="./knowledge_base/Homicides_2001_to_present.csv",
        help="Path to the homicide CSV file"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run in test mode to verify data loading and tool functionality"
    )
    args = parser.parse_args()
    
    # Initialize the homicide data
    try:
        homicide_data = HomicideDataMCP(args.csv_path)
        print(f"✅ Homicide MCP server initialized successfully")
        
        if args.test:
            print("\n🧪 Testing tools...")
            
            # Test statistics
            print("\n📊 Testing statistics...")
            stats = handle_tool_call("get_homicide_statistics", {})
            print(f"Total homicides: {stats.get('total_homicides', 'Unknown')}")
            print(f"Year range: {stats.get('year_range', 'Unknown')}")
            
            # Test year query
            print("\n📅 Testing year query (2023)...")
            year_data = handle_tool_call("get_homicides_by_year", {"year": 2023, "limit": 5})
            print(f"Found {year_data.get('total_records', 0)} records for 2023")
            
            # Test IUCR info
            print("\n📋 Testing IUCR info...")
            iucr_data = handle_tool_call("get_iucr_info", {})
            print(f"Unique IUCR codes: {iucr_data.get('unique_codes_count', 'Unknown')}")
            
            # Test location search
            print("\n🔍 Testing location search...")
            location_data = handle_tool_call("search_by_location", {"location_query": "STREET", "limit": 3})
            print(f"Found {location_data.get('total_matches', 0)} street homicides")
            
            print("\n✅ All tests completed successfully!")
        else:
            print("Use --test flag to run functionality tests")
            print("Available tools:", [tool.name for tool in create_homicide_tools()])
            
    except Exception as e:
        print(f"❌ Error initializing homicide data: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
