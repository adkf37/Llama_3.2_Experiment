# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

This is a Local LLM system with Model Context Protocol (MCP) integration for intelligent homicide data analysis. The system combines a local Ollama LLM with MCP tools to enable natural language querying of Chicago homicide data from 2001 to present.

**Key Architecture:**
- Local LLM via Ollama (no external API calls)
- MCP-based tool calling system for structured data analysis
- Intelligent question detection and tool routing
- Chicago homicide dataset with 12,657+ records

## Development Commands

### Essential Setup
```powershell
# Install dependencies
pip install -r requirements.txt

# Run automated setup (installs deps, checks Ollama, pulls model)
python setup.py

# Check if model is available/pull model manually
ollama pull llama3.2:3b
# Alternative models: gemma2:9b, mistral:7b, qwen3:8b
```

### Running the Application
```powershell
# Start interactive CLI (primary interface)
python main.py

# Ask a single question via command line
python main.py --question "What location had the most homicides?"

# Run in setup mode to verify model availability
python main.py --setup
```

### Testing MCP Tools
```powershell
# Test homicide data MCP functionality
python homicide_mcp.py --test

# Test specific MCP tool integration
python mcp_integration.py
```

### Configuration Management
```powershell
# Configuration is managed via config.yaml
# Key settings:
# - model.name: Ollama model to use
# - model.temperature: Response creativity (0.0-2.0)
# - model.max_tokens: Maximum response length
```

## Core Architecture

### Main Components
1. **`main.py`** - Application entry point with interactive CLI and command routing
2. **`intelligent_mcp.py`** - Intelligent MCP handler that parses LLM responses and routes tool calls
3. **`mcp_integration.py`** - MCP protocol implementation and tool management layer
4. **`homicide_mcp.py`** - Core data analysis engine with Chicago homicide dataset tools
5. **`llama_client.py`** - Ollama client wrapper with tool calling capabilities
6. **`config.py`** - Configuration management system using YAML

### MCP Tool System
The system exposes two MCP tools for clarity and reliability:

- **`query_homicides_advanced`** - Single, flexible data query tool for ALL homicide data analysis (years, ranges, ward/district/community filters, arrests, domestic, location types)
- **`get_iucr_info`** - IUCR code information and explanations (education-oriented)

#### Advanced Query Capabilities
The `query_homicides_advanced` tool supports complex queries with multiple filters and focused results:

**Geographic Filters:**
- Ward (1-50)
- District (1-25) 
- Community Area (1-77)

**Temporal Filters:**
- Start year / End year (date ranges)

**Status Filters:**
- Arrest status (true/false)
- Domestic violence cases (true/false)
- Location type (STREET, APARTMENT, RESIDENCE, etc.)

**Result Control Parameters:**
- `group_by` - Focus on specific dimension: "ward", "district", "community_area", or "location"
- `top_n` - Control number of items shown in breakdowns (default 10, max 50)

**Enhanced "Which X had the most" Queries:**
Using `group_by` provides focused, direct answers with highlighted results.

**Example Queries by Type:**

**"Which X had the most" queries (uses `group_by`):**
- "Which ward had the most homicides in 2013?" → `query_homicides_advanced` + `group_by: ward`
- "What district had the most homicides from 2020-2022?" → `query_homicides_advanced` + `group_by: district`  
- "Show top 3 community areas with domestic homicides" → `query_homicides_advanced` + `group_by: community_area` + `top_n: 3`

**Multi-criteria filtering:**
- "How many homicides from 2015-2019 in ward 3?" → `query_homicides_advanced`
- "Show homicides in district 11 where arrests were made" → `query_homicides_advanced`
- "Find domestic violence homicides on the street" → `query_homicides_advanced`

**General queries:**
- "How many homicides in 2023?" → `query_homicides_advanced`
- "What are the overall statistics?" → `query_homicides_advanced`
- "What does IUCR mean?" → `get_iucr_info`

### Intelligent Question Routing
The system automatically detects homicide-related questions using keyword analysis and routes them through the MCP tool system. Non-data questions are handled by the base LLM without tools.

**Keywords that trigger MCP tools:** homicide, murder, killing, crime, arrest, location, year, statistics, iucr, police, data, "how many", "what location", "which", ward, district, "community area", domestic, "from [year] to [year]", "where arrests", "no arrests"

### Tool Call Flow
1. User asks natural language question
2. `intelligent_mcp.py` sends question to LLM with tool descriptions
3. LLM responds with either direct answer or `TOOL_CALL:` JSON
4. System parses tool call and executes via `homicide_mcp.py`
5. Tool result is formatted and sent back to LLM for final response synthesis

## Data Structure

### Primary Dataset
- **File:** `knowledge_base/Homicides_2001_to_present.csv`
- **Records:** 12,657+ homicide cases from 2001-present
- **Schema:** See `knowledge_base/homicides_schema.md` for detailed field descriptions

### Key Data Fields
- **Geographic:** District, Ward, Community Area, Beat, Block, Coordinates
- **Temporal:** Date, Year 
- **Case Details:** Case Number, IUCR Code, Primary Type, Description
- **Investigation:** Arrest status, Domestic flag
- **Location Context:** Location Description (STREET, APARTMENT, etc.)

## Configuration Management

### Model Configuration (`config.yaml`)
```yaml
model:
  name: "llama3.2:3b"        # Ollama model name
  temperature: 0.7           # Response creativity
  max_tokens: 2048          # Max response length
  top_p: 0.9                # Nucleus sampling
  context_window: 8192      # Model context size
```

### Recommended Models by Use Case
- **Development/Testing:** `llama3.2:3b` (fast, good balance)
- **Production/Quality:** `gemma2:9b` (more capable, larger)
- **Alternative:** `mistral:7b`, `qwen3:8b`

## Interactive CLI Commands

### Data Analysis Commands
- **Direct Questions:** "What location had the most homicides?", "How many homicides in 2023?"
- **`/mcp-tools`** - List all available MCP tools with descriptions
- **`/mcp <tool> [args]`** - Manual MCP tool execution
- **`/notools <question>`** - Use base model without MCP tools

### System Commands  
- **`/config`** - Show current model and system configuration
- **`/temp <value>`** - Set temperature (0.0-2.0) for response creativity
- **`/help`** - Display all available commands and usage examples
- **`/quit`** - Exit application

## Error Handling & Debugging

### JSON Parsing Robustness
The system includes advanced JSON parsing for tool calls with multiple fallback mechanisms:
- Brace counting with quote awareness
- Escape character handling  
- Fallback regex extraction
- Malformed JSON recovery

### Common Issues
- **Model not found:** Run `ollama pull <model_name>` 
- **CSV not found:** Ensure `knowledge_base/Homicides_2001_to_present.csv` exists
- **Tool call parsing errors:** Check LLM temperature (lower = more structured responses)

## Development Notes

### Migration from RAG Architecture
This project evolved from a RAG (Retrieval Augmented Generation) system to MCP-based structured data analysis:
- **Legacy:** Vector embeddings, ChromaDB storage (still present in config but unused)
- **Current:** Direct data analysis with pandas, structured tool calls
- **Benefits:** More precise answers, better data insights, lower computational overhead

### Code Patterns
- **Tool calling:** LLM responds with `TOOL_CALL: {"name": "...", "arguments": {...}}` format
- **Response synthesis:** Tool results are fed back to LLM for natural language formulation  
- **Error recovery:** Graceful fallbacks when tool calls fail or are malformed
- **Type safety:** Extensive use of typing hints and cast operations for Ollama client

### Data Processing
- **Date parsing:** Handles "MM/dd/yyyy HH:mm:ss AM/PM" format with error handling
- **Boolean conversion:** Robust string-to-boolean for Arrest/Domestic flags
- **Type coercion:** Safe conversion of pandas types to JSON-serializable formats

## Dependencies & Requirements

### Core Dependencies
- **ollama** - Local LLM client
- **pandas** - Data analysis and CSV processing  
- **mcp** - Model Context Protocol support
- **pyyaml** - Configuration management
- **requests** - HTTP client utilities

### Legacy Dependencies (RAG system remnants)
- **chromadb**, **sentence-transformers**, **langchain** - Vector database support (unused)
- **streamlit** - Web interface (legacy, unused)
