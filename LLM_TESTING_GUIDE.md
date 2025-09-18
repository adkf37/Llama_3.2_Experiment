# LLM Testing Guide for MCP Tools

This guide explains how to test different Large Language Models with the MCP-based homicide data analysis tools.

## 🎯 Why Test Different Models?

Different LLMs have varying capabilities:
- **Tool calling accuracy** - Some models better understand when to use tools
- **Parameter extraction** - Ability to parse complex queries into correct parameters  
- **JSON generation** - Reliability in generating valid tool call JSON
- **Instruction following** - How well they follow system prompts
- **Response speed** - Trade-offs between capability and performance

## 🚀 Quick Start

### 1. Install Models to Test
```powershell
# Recommended starter set
ollama pull llama3.2:3b      # Good baseline
ollama pull gemma2:9b        # Large, capable
ollama pull mistral:7b       # Instruction-following
ollama pull phi3:mini        # Efficient

# Optional: smaller/larger models
ollama pull llama3.2:1b      # Fastest
ollama pull qwen2.5:7b       # Alternative
```

### 2. Run the Test Suite
```powershell
python test_llm_performance.py
```

This will:
- Auto-detect available models
- Run standardized test cases
- Generate performance scores
- Save detailed results to JSON
- Show comparative analysis

## 📊 Understanding Results

### Test Categories

**Simple Queries (Expected: 80-98% success)**
- Single tool calls with clear parameters
- Examples: "How many homicides in 2023?", "What does IUCR mean?"

**"Which X Most" Queries (Expected: 60-95% success)**  
- Requires `group_by` parameter usage
- Examples: "Which ward had the most homicides in 2013?"

**Top N Queries (Expected: 60-95% success)**
- Combines `group_by` + `top_n` parameters
- Examples: "Show top 3 districts from 2020-2022"

**Complex Multi-Criteria (Expected: 40-90% success)**
- Multiple filter parameters + grouping
- Examples: "Top 2 wards with no arrests made"

### Performance Indicators

**✅ Success Indicators:**
- Tool call executed successfully
- Correct tool selection
- Valid JSON generation
- Appropriate parameters used

**❌ Failure Indicators:**
- No tool call generated
- Wrong tool selected
- Malformed JSON
- Missing required parameters
- Timeout/errors

## 📋 Model Categories & Expected Performance

### Small Models (1-3B parameters)
- **Examples:** llama3.2:1b, gemma2:2b, llama3.2:3b
- **Speed:** Very Fast
- **Capability:** Basic to Good
- **Issues:** May struggle with complex JSON, parameter confusion
- **Best for:** Quick responses, simple queries

### Medium Models (4-8B parameters)  
- **Examples:** mistral:7b, qwen2.5:7b, llama3.1:8b
- **Speed:** Moderate
- **Capability:** Good to Excellent
- **Issues:** Occasional parameter errors
- **Best for:** Balanced performance, most use cases

### Large Models (9B+ parameters)
- **Examples:** gemma2:9b, mistral-nemo, qwen2.5:14b
- **Speed:** Slower
- **Capability:** Excellent
- **Issues:** Resource intensive
- **Best for:** Complex queries, high accuracy needs

## 🔧 Customizing Tests

### Adding New Test Cases

Edit `test_llm_performance.py` to add new test scenarios:

```python
"your_category": [
    {
        "question": "Your test question here",
        "expected_tool": "query_homicides_advanced",
        "expected_params": ["param1", "param2"],
        "complexity": "medium"
    }
]
```

### Testing Specific Models

```python
# Modify the models_to_test list in test_llm_performance.py
self.models_to_test = [
    "your-specific-model:tag",
    "another-model:version"
]
```

### Configuration Tweaks

Edit your `config.yaml` to test different model parameters:
```yaml
model:
  temperature: 0.3  # Lower = more consistent
  top_p: 0.9
  max_tokens: 2048
```

## 📈 Analyzing Results

### JSON Output Structure
```json
{
  "test_suite_version": "1.0",
  "timestamp": "2024-XX-XX",
  "models_tested": [
    {
      "model": "llama3.2:3b", 
      "overall_score": 85.7,
      "categories": {
        "simple_queries": [...],
        "which_x_most_queries": [...] 
      }
    }
  ],
  "summary": {
    "best_model": "gemma2:9b",
    "average_score": 78.4,
    "models_by_score": [...]
  }
}
```

### Key Metrics to Watch
- **Overall Score** - Percentage of tests passed
- **Response Time** - Average milliseconds per query
- **Category Performance** - Success rate by complexity
- **Error Patterns** - Common failure modes

## 🎯 Optimization Tips

### For Better Performance
1. **Lower temperature** (0.1-0.3) for more consistent tool calls
2. **Increase max_tokens** if responses are cut off
3. **Use system prompts** with clear examples
4. **Test with your specific use cases** beyond the standard suite

### For Different Use Cases
- **Speed-critical:** Use smaller models (1-3B)
- **Accuracy-critical:** Use larger models (9B+)
- **Balanced:** Medium models (4-8B) often optimal
- **Code-heavy:** Try code-specialized models

## 🚨 Troubleshooting

### Common Issues

**Model fails to load:**
- Check if model is installed: `ollama list`
- Verify model name/tag is correct
- Ensure sufficient system resources

**All tests fail:**
- Check if MCP data is loaded properly
- Verify config.yaml is valid
- Test with working model first (llama3.2:3b)

**Inconsistent results:**
- Lower temperature for more consistency
- Run tests multiple times
- Check for system resource constraints

**JSON parsing errors:**
- Some models struggle with JSON - this is expected
- Consider different system prompts for problematic models
- Document which models need special handling

## 💡 Best Practices

1. **Test systematically** - Run the same tests on multiple models
2. **Consider your use case** - Speed vs accuracy trade-offs
3. **Document findings** - Keep notes on model-specific behaviors  
4. **Version control** - Tag model versions that work well
5. **Monitor resources** - Larger models need more RAM/VRAM
6. **Update regularly** - New model versions often improve tool calling

## 📚 Further Reading

- Check `model_configs.yaml` for detailed model specifications
- Review test results JSON files for patterns
- Monitor Ollama releases for new models
- Consider fine-tuning for your specific domain

Happy testing! 🧪
