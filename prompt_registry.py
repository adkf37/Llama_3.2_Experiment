"""Central registry for system prompt variants used by LlamaClient."""

from typing import Any, Dict, List
import json

PROMPT_VARIANTS: Dict[str, Dict[str, Any]] = {
    "tool_use_v1": {
        "template": (
            "You are a data analyst assistant for Chicago homicide data.\n"
            "Use the provided tools to ground your answers in factual statistics.\n\n"
            "Available tools:\n"
            "{tool_summaries}\n\n"
            "Guidelines for tool usage:\n"
            "{guidelines}\n\n"
            "When a tool is required respond ONLY with a JSON object prefixed by 'TOOL_CALL:' on the same line.\n"
            "Format: TOOL_CALL: {{\"name\": \"tool_name\", \"arguments\": {{...}}}}\n\n"
            "Examples:\n"
            "{examples}\n\n"
            "If a tool is not required, answer normally."
        ),
        "guidelines": [
            "Prefer `query_homicides_advanced` for any question about counts, trends, rankings, or filtered views.",
            "Use `get_iucr_info` strictly for IUCR code explanations or taxonomy questions.",
            "Always include `start_year`/`end_year` when a user references a specific year or range.",
            "For 'which/what had the most' style questions set `group_by` to ward, district, community_area, or location as appropriate.",
            "Supply integers for numeric parameters and `true`/`false` for booleans."
        ],
        "examples": [
            {
                "question": "How many homicides in 2023?",
                "tool": "query_homicides_advanced",
                "arguments": {"start_year": 2023, "end_year": 2023}
            },
            {
                "question": "Which district had the most homicides from 2020-2022?",
                "tool": "query_homicides_advanced",
                "arguments": {"start_year": 2020, "end_year": 2022, "group_by": "district"}
            },
            {
                "question": "What does IUCR mean?",
                "tool": "get_iucr_info",
                "arguments": {}
            }
        ]
    },
    "tool_use_reasoned": {
        "template": (
            "You are an expert homicide data analyst.\n"
            "Before selecting a tool, briefly reflect on the user's goal and required parameters.\n"
            "Keep the reflection concise (one sentence) and then respond with the tool call if needed.\n\n"
            "Available tools:\n"
            "{tool_summaries}\n\n"
            "Reasoning and tool usage rules:\n"
            "{guidelines}\n\n"
            "When a tool is required respond ONLY with a JSON object prefixed by 'TOOL_CALL:' on the same line.\n"
            "Format: TOOL_CALL: {{\"name\": \"tool_name\", \"arguments\": {{...}}}}\n\n"
            "Examples:\n"
            "{examples}\n\n"
            "If a tool is not required, answer normally with a concise explanation."
        ),
        "guidelines": [
            "State the reasoning for the chosen tool before the tool call (e.g., 'Need year-filtered homicide counts so calling ...').",
            "Map user questions about counts or rankings to `query_homicides_advanced` with appropriate filters.",
            "Use `group_by` whenever the user asks for \"which\" entity had the most or for top-N rankings.",
            "Use `get_iucr_info` for definitional IUCR questions and avoid mixing it with quantitative analysis.",
            "Return to natural language answers after executing the tool by summarizing the results."
        ],
        "examples": [
            {
                "reasoning": "Need filtered stats for 2021, use query_homicides_advanced.",
                "tool": "query_homicides_advanced",
                "arguments": {"start_year": 2021, "end_year": 2021}
            },
            {
                "reasoning": "User wants IUCR explanation, call get_iucr_info.",
                "tool": "get_iucr_info",
                "arguments": {}
            }
        ]
    }
}


def _summarize_tool(tool: Dict[str, Any]) -> str:
    name = tool.get("name", "unknown_tool")
    description = tool.get("description", "")
    params = tool.get("parameters", {}) or {}
    required = set(tool.get("required", []) or [])

    if not params:
        return f"- {name}: {description}"

    param_summaries = []
    for param_name, param_info in params.items():
        hint = param_info.get("description", "")
        if param_name in required:
            hint = f"{hint} (required)" if hint else "required"
        param_summaries.append(f"{param_name}: {hint}".strip())

    params_text = "; ".join(param_summaries)
    return f"- {name}: {description}\n  Parameters: {params_text}"


def _format_examples(examples: List[Any]) -> List[str]:
    formatted: List[str] = []
    for example in examples:
        if isinstance(example, str):
            formatted.append(example)
            continue

        if not isinstance(example, dict):
            continue

        call_payload = json.dumps(
            {
                "name": example.get("tool"),
                "arguments": example.get("arguments", {})
            },
            ensure_ascii=False
        )

        if "reasoning" in example:
            formatted.append(f"- Reasoning: \"{example['reasoning']}\"\n  TOOL_CALL: {call_payload}")
        else:
            formatted.append(f"- Question: \"{example.get('question', 'Unknown question')}\"\n  TOOL_CALL: {call_payload}")
    return formatted


def build_tool_system_prompt(variant: str, tools: List[Dict[str, Any]]) -> str:
    """Build a system prompt for tool usage based on a registered variant."""
    variant_config = PROMPT_VARIANTS.get(variant, PROMPT_VARIANTS["tool_use_v1"])

    tool_lines = [_summarize_tool(tool) for tool in tools] if tools else ["- No tools available"]
    tool_section = "\n".join(tool_lines)

    guidelines = [str(rule) for rule in variant_config.get("guidelines", [])]
    guidelines_section = "\n".join(f"- {rule}" for rule in guidelines) if guidelines else "- Follow standard best practices."

    example_entries = variant_config.get("examples", [])
    example_lines = _format_examples(example_entries)
    examples_section = "\n".join(example_lines) if example_lines else "(No examples configured)"

    template = variant_config.get("template", PROMPT_VARIANTS["tool_use_v1"]["template"])
    return template.format(
        tool_summaries=tool_section,
        guidelines=guidelines_section,
        examples=examples_section
    )
