#!/usr/bin/env python3
"""
LLM Performance Test Suite for MCP Tools
Tests different models on various query types and complexity levels.
"""

import json
import time
from typing import Dict, List, Any, Tuple
from datetime import datetime
from pathlib import Path

from llama_client import LlamaClient
from intelligent_mcp import intelligent_mcp

class LLMPerformanceTester:
    """Test suite for evaluating LLM performance with MCP tools."""
    
    def __init__(self):
        self.test_results = []
        self.models_to_test = [
            "llama3.2:3b",
            "gemma3:12b",
            "gemma3:270M"
            "mistral:latest",
            "qwen3:8b",
            # Add more models as available
        ]
        
        # Test cases organized by complexity and type
        self.test_cases = {
            "simple_queries": [
                {
                    "question": "How many homicides in 2023?",
                    "expected_tool": "query_homicides_advanced",
                    "expected_params": ["start_year", "end_year"],
                    "complexity": "simple"
                },
                {
                    "question": "What does IUCR mean?",
                    "expected_tool": "get_iucr_info", 
                    "expected_params": [],
                    "complexity": "simple"
                }
            ],
            "which_x_most_queries": [
                {
                    "question": "Which ward had the most homicides in 2013?",
                    "expected_tool": "query_homicides_advanced",
                    "expected_params": ["start_year", "end_year", "group_by"],
                    "expected_group_by": "ward",
                    "complexity": "medium"
                },
                {
                    "question": "What district had the most homicides from 2020 to 2022?",
                    "expected_tool": "query_homicides_advanced", 
                    "expected_params": ["start_year", "end_year", "group_by"],
                    "expected_group_by": "district",
                    "complexity": "medium"
                }
            ],
            "top_n_queries": [
                {
                    "question": "Show me the top 3 districts with the most homicides from 2020 to 2022",
                    "expected_tool": "query_homicides_advanced",
                    "expected_params": ["start_year", "end_year", "group_by", "top_n"],
                    "expected_group_by": "district",
                    "expected_top_n": 3,
                    "complexity": "medium"
                }
            ],
            "complex_multi_criteria": [
                {
                    "question": "What are the top 2 wards with the most homicides where no arrests were made?",
                    "expected_tool": "query_homicides_advanced",
                    "expected_params": ["arrest_status", "group_by", "top_n"],
                    "expected_group_by": "ward",
                    "expected_top_n": 2,
                    "expected_arrest_status": False,
                    "complexity": "complex"
                },
                {
                    "question": "Show me the top 5 community areas with domestic homicides",
                    "expected_tool": "query_homicides_advanced",
                    "expected_params": ["domestic", "group_by", "top_n"],
                    "expected_group_by": "community_area",
                    "expected_top_n": 5,
                    "expected_domestic": True,
                    "complexity": "complex"
                }
            ]
        }
    
    def test_model(self, model_name: str) -> Dict[str, Any]:
        """Test a specific model against all test cases."""
        print(f"\n🧪 Testing model: {model_name}")
        print("=" * 50)
        
        try:
            client = LlamaClient(model_name=model_name)
            model_results = {
                "model": model_name,
                "timestamp": datetime.now().isoformat(),
                "categories": {},
                "overall_score": 0,
                "total_tests": 0,
                "passed_tests": 0,
                "errors": []
            }
            
            for category, test_cases in self.test_cases.items():
                print(f"\n📋 Testing {category}...")
                category_results = []
                
                for i, test_case in enumerate(test_cases, 1):
                    print(f"  {i}. {test_case['question'][:50]}...")
                    result = self.run_single_test(client, test_case)
                    category_results.append(result)
                    
                    model_results["total_tests"] += 1
                    if result["passed"]:
                        model_results["passed_tests"] += 1
                    
                    if result.get("error"):
                        model_results["errors"].append({
                            "question": test_case["question"],
                            "error": result["error"]
                        })
                
                model_results["categories"][category] = category_results
            
            # Calculate overall score
            if model_results["total_tests"] > 0:
                model_results["overall_score"] = (
                    model_results["passed_tests"] / model_results["total_tests"]
                ) * 100
            
            return model_results
            
        except Exception as e:
            return {
                "model": model_name,
                "error": f"Failed to initialize model: {str(e)}",
                "overall_score": 0
            }
    
    def run_single_test(self, client: LlamaClient, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single test case and evaluate the result."""
        start_time = time.time()
        result = {
            "question": test_case["question"],
            "complexity": test_case["complexity"],
            "passed": False,
            "response_time": 0,
            "tool_called": None,
            "parameters_used": {},
            "issues": []
        }
        
        try:
            # Generate response using the intelligent MCP handler
            response = intelligent_mcp.handle_question_with_tools(
                test_case["question"], client
            )
            
            result["response_time"] = time.time() - start_time
            result["response"] = response[:200] + "..." if len(response) > 200 else response
            
            # Check if it appears a successful tool call was made
            if "Advanced Homicide Query Results" in response or "IUCR" in response:
                result["tool_called"] = "success"
                result["passed"] = True
            else:
                result["issues"].append("No clear tool call result detected")
            
            # Additional validation could be added here to check specific parameters
            
        except Exception as e:
            result["error"] = str(e)
            result["response_time"] = time.time() - start_time
        
        return result
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run tests on all available models."""
        print("🚀 Starting LLM Performance Test Suite")
        print("=" * 60)
        
        all_results = {
            "test_suite_version": "1.0",
            "timestamp": datetime.now().isoformat(),
            "models_tested": [],
            "summary": {}
        }
        
        # Check which models are actually available
        available_models = self.check_available_models()
        
        for model in available_models:
            try:
                model_results = self.test_model(model)
                all_results["models_tested"].append(model_results)
                
                print(f"\n✅ {model}: {model_results.get('overall_score', 0):.1f}% pass rate")
                
            except Exception as e:
                print(f"\n❌ {model}: Failed to test - {e}")
                all_results["models_tested"].append({
                    "model": model,
                    "error": str(e),
                    "overall_score": 0
                })
        
        # Generate summary
        all_results["summary"] = self.generate_summary(all_results["models_tested"])
        
        return all_results
    
    def check_available_models(self) -> List[str]:
        """Check which models are actually available locally."""
        print("🔍 Checking available models...")
        available = []
        
        try:
            import subprocess
            result = subprocess.run(
                ["ollama", "list"], 
                capture_output=True, 
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                for line in lines:
                    if line.strip():
                        model_name = line.split()[0]
                        if model_name in self.models_to_test:
                            available.append(model_name)
                            print(f"  ✅ {model_name}")
                        
            if not available:
                print("  ⚠️  No test models found, will try default models")
                available = ["llama3.2:3b"]  # Fallback
                
        except Exception as e:
            print(f"  ❌ Error checking models: {e}")
            available = ["llama3.2:3b"]  # Fallback
        
        return available
    
    def generate_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a summary of all test results."""
        summary = {
            "best_model": None,
            "worst_model": None,
            "average_score": 0,
            "models_by_score": []
        }
        
        valid_results = [r for r in results if "overall_score" in r and not r.get("error")]
        
        if valid_results:
            # Sort by score
            sorted_results = sorted(valid_results, key=lambda x: x["overall_score"], reverse=True)
            
            summary["best_model"] = sorted_results[0]["model"]
            summary["worst_model"] = sorted_results[-1]["model"]
            summary["average_score"] = sum(r["overall_score"] for r in valid_results) / len(valid_results)
            summary["models_by_score"] = [(r["model"], r["overall_score"]) for r in sorted_results]
        
        return summary
    
    def save_results(self, results: Dict[str, Any], filename: str = None):
        """Save test results to a JSON file."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"llm_test_results_{timestamp}.json"
        
        filepath = Path(filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Results saved to: {filepath.absolute()}")
    
    def print_detailed_report(self, results: Dict[str, Any]):
        """Print a detailed report of the test results."""
        print("\n" + "="*60)
        print("📊 DETAILED TEST RESULTS REPORT")
        print("="*60)
        
        summary = results["summary"]
        
        print(f"\n🏆 SUMMARY:")
        print(f"  Best Model: {summary.get('best_model', 'N/A')}")
        print(f"  Average Score: {summary.get('average_score', 0):.1f}%")
        
        print(f"\n📈 MODELS BY PERFORMANCE:")
        for model, score in summary.get("models_by_score", []):
            print(f"  {model}: {score:.1f}%")
        
        print(f"\n📋 DETAILED BREAKDOWN:")
        for model_result in results["models_tested"]:
            if model_result.get("error"):
                print(f"\n❌ {model_result['model']}: ERROR - {model_result['error']}")
                continue
            
            model = model_result["model"]
            score = model_result.get("overall_score", 0)
            passed = model_result.get("passed_tests", 0)
            total = model_result.get("total_tests", 0)
            
            print(f"\n📊 {model} ({score:.1f}% - {passed}/{total})")
            
            for category, cat_results in model_result.get("categories", {}).items():
                category_passed = sum(1 for r in cat_results if r.get("passed", False))
                category_total = len(cat_results)
                print(f"  {category}: {category_passed}/{category_total}")
                
                for test in cat_results:
                    status = "✅" if test.get("passed", False) else "❌"
                    time_ms = test.get("response_time", 0) * 1000
                    print(f"    {status} {test['question'][:40]}... ({time_ms:.0f}ms)")
                    
                    if test.get("issues"):
                        for issue in test["issues"]:
                            print(f"        ⚠️  {issue}")

def main():
    """Main function to run the test suite."""
    tester = LLMPerformanceTester()
    
    print("This will test different LLMs with the MCP homicide data tools.")
    print("Make sure you have the models installed with: ollama pull <model_name>")
    
    # Run all tests
    results = tester.run_all_tests()
    
    # Save results
    tester.save_results(results)
    
    # Print detailed report
    tester.print_detailed_report(results)
    
    print(f"\n🎉 Testing complete! Check the JSON file for detailed results.")

if __name__ == "__main__":
    main()
