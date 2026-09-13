"""Product Comparison Assistant with a traceable ReAct loop."""

import json
import os
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mcp_server import MCPProductServer
from prompts import CHATBOT_BASELINE_PROMPT, MAX_ITERATIONS, REACT_AGENT_SYSTEM_PROMPT
from providers import BaseLLMProvider, get_llm_provider

load_dotenv()

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def load_test_cases() -> List[Dict[str, Any]]:
    """Load the customized five-case acceptance suite."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "test_cases.json")
    with open(config_path, "r", encoding="utf-8") as file:
        return json.load(file)


def save_waterfall_trace(trace_data: List[Dict[str, Any]]) -> None:
    """Persist execution evidence for the submission report."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    trace_path = os.path.join(base_dir, "docs", "trace_waterfall.json")
    with open(trace_path, "w", encoding="utf-8") as file:
        json.dump(trace_data, file, ensure_ascii=False, indent=2)
    print(f"Trace saved: {trace_path} ({len(trace_data)} events)")


def run_baseline_chatbot(user_query: str, provider: BaseLLMProvider) -> str:
    """Run the level-2 baseline without tool access."""
    response = provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT)
    print(f"\n[CHATBOT BASELINE]\n{response}")
    return response


def _build_iteration_prompt(user_query: str, history: List[Dict[str, Any]]) -> str:
    if not history:
        return user_query
    history_json = json.dumps(history, ensure_ascii=False, indent=2)
    return (
        f"YÊU CẦU GỐC:\n{user_query}\n\n"
        f"LỊCH SỬ REACT:\n{history_json}\n\n"
        "Dựa trên Observation gần nhất, hãy gọi công cụ tiếp theo nếu còn việc cần làm; "
        "nếu đã đủ dữ liệu hoặc gặp lỗi thì trả lời cuối cùng."
    )


def run_react_agent(
    user_query: str,
    provider: BaseLLMProvider,
    mcp_server: MCPProductServer,
) -> List[Dict[str, Any]]:
    """Execute Thought -> Action -> Observation until a final answer or a safe stop."""
    print(f"\n[REACT AGENT] {user_query}")
    trace_logs: List[Dict[str, Any]] = []
    history: List[Dict[str, Any]] = []
    seen_actions = set()

    for step in range(1, MAX_ITERATIONS + 1):
        started_at = time.perf_counter()
        iteration_prompt = _build_iteration_prompt(user_query, history)
        llm_response = provider.generate_with_tools(
            iteration_prompt,
            mcp_server.list_tools(),
            system_prompt=REACT_AGENT_SYSTEM_PROMPT,
        )
        llm_latency_ms = round((time.perf_counter() - started_at) * 1000, 2)
        response_type = llm_response.get("type")
        thought = llm_response.get("thought", "Không có mô tả quyết định.")
        print(f"Step {step} | Thought: {thought}")

        if response_type == "text":
            content = llm_response.get("content", "").strip()
            trace_logs.append({
                "step": step,
                "query": user_query,
                "action_type": "FINAL_ANSWER",
                "thought": thought,
                "output": content,
                "llm_latency_ms": llm_latency_ms,
            })
            print(f"Final: {content}")
            return trace_logs

        if response_type == "error":
            message = llm_response.get("content", "LLM provider returned an unknown error.")
            trace_logs.append({
                "step": step,
                "query": user_query,
                "action_type": "PROVIDER_ERROR",
                "thought": thought,
                "error": message,
                "llm_latency_ms": llm_latency_ms,
            })
            print(f"Provider error: {message}")
            return trace_logs

        if response_type != "tool_call":
            trace_logs.append({
                "step": step,
                "query": user_query,
                "action_type": "INVALID_LLM_RESPONSE",
                "output": llm_response,
                "llm_latency_ms": llm_latency_ms,
            })
            print("Invalid provider response; stopped safely.")
            return trace_logs

        tool_name = llm_response.get("tool_name", "")
        arguments = llm_response.get("arguments", {})
        action_signature = json.dumps(
            {"tool_name": tool_name, "arguments": arguments},
            ensure_ascii=False,
            sort_keys=True,
        )
        if action_signature in seen_actions:
            trace_logs.append({
                "step": step,
                "query": user_query,
                "action_type": "REPEATED_ACTION_STOP",
                "tool_name": tool_name,
                "arguments": arguments,
                "llm_latency_ms": llm_latency_ms,
            })
            print("Repeated identical action detected; stopped safely.")
            return trace_logs
        seen_actions.add(action_signature)

        tool_started_at = time.perf_counter()
        mcp_result = mcp_server.call_tool(tool_name, arguments)
        tool_latency_ms = round((time.perf_counter() - tool_started_at) * 1000, 2)
        observation = mcp_result.get("result", {})
        trace_logs.append({
            "step": step,
            "query": user_query,
            "action_type": "TOOL_EXECUTION",
            "thought": thought,
            "tool_name": tool_name,
            "arguments": arguments,
            "observation": observation,
            "llm_latency_ms": llm_latency_ms,
            "tool_latency_ms": tool_latency_ms,
        })
        history.append({
            "action": tool_name,
            "arguments": arguments,
            "observation": observation,
        })
        print(f"Action: {tool_name}({json.dumps(arguments, ensure_ascii=False)})")
        print(f"Observation status: {observation.get('status', 'UNKNOWN')}")

    trace_logs.append({
        "step": MAX_ITERATIONS + 1,
        "query": user_query,
        "action_type": "MAX_ITERATIONS_REACHED",
        "output": "Agent dừng vì đã đạt giới hạn vòng lặp.",
    })
    print("Maximum iteration limit reached; stopped safely.")
    return trace_logs


def validate_trace(test_case: Dict[str, Any], trace: List[Dict[str, Any]]) -> Tuple[bool, str]:
    """Validate observable behavior instead of merely counting executed tests."""
    tool_events = [event for event in trace if event.get("action_type") == "TOOL_EXECUTION"]
    tool_names = [event.get("tool_name") for event in tool_events]
    statuses = [event.get("observation", {}).get("status") for event in tool_events]
    has_final = any(event.get("action_type") == "FINAL_ANSWER" for event in trace)
    case_type = test_case["type"]

    if case_type == "direct_query":
        passed = not tool_events and has_final
        return passed, "expected a direct final answer without tools"
    if case_type == "single_tool_query":
        passed = tool_names == ["search_products"] and statuses == ["SUCCESS"] and has_final
        return passed, "expected one successful search_products call"
    if case_type == "comparison_report_creation":
        passed = tool_names == ["create_comparison_report"] and statuses == ["SUCCESS"] and has_final
        return passed, "expected one successful create_comparison_report call"
    if case_type == "multi_step_reasoning":
        passed = (
            tool_names == ["search_products", "create_comparison_report"]
            and statuses == ["SUCCESS", "SUCCESS"]
            and has_final
        )
        return passed, "expected search then report creation, both successful"
    if case_type == "edge_case_handling":
        passed = (
            tool_names == ["create_comparison_report"]
            and statuses == ["INVALID_PRODUCT"]
            and has_final
        )
        return passed, "expected INVALID_PRODUCT followed by a clear final answer"
    return False, f"unknown test type: {case_type}"


def run_test_suite(
    tests: List[Dict[str, Any]],
    provider: BaseLLMProvider,
    mcp_server: MCPProductServer,
) -> Tuple[int, List[str]]:
    all_traces: List[Dict[str, Any]] = []
    failed_cases: List[str] = []
    run_started_at = datetime.now(timezone.utc).isoformat()
    provider_metadata = {
        "provider": provider.__class__.__name__,
        "model": getattr(provider, "model_name", "unknown"),
        "run_started_at_utc": run_started_at,
    }

    for test_case in tests:
        print(f"\n{'=' * 60}\n[{test_case['id']}] {test_case['question']}")
        logs = run_react_agent(test_case["question"], provider, mcp_server)
        passed, expectation = validate_trace(test_case, logs)
        print(f"Result: {'PASS' if passed else 'FAIL'} | {expectation}")
        if not passed:
            failed_cases.append(test_case["id"])
        for event in logs:
            all_traces.append({
                "test_case_id": test_case["id"],
                **provider_metadata,
                **event,
            })

    save_waterfall_trace(all_traces)
    return len(tests) - len(failed_cases), failed_cases


def main() -> int:
    provider = get_llm_provider()
    mcp_server = MCPProductServer()
    tests = load_test_cases()
    model_name = getattr(provider, "model_name", "unknown")

    print("PRODUCT COMPARISON ASSISTANT - DAY 03 LAB")
    print(f"Provider: {provider.__class__.__name__} | Model: {model_name}")
    print(f"MCP server: {mcp_server.server_name}")
    if provider.__class__.__name__ == "MockOfflineProvider":
        print("NOTICE: Đây chỉ là preflight offline, chưa phải bằng chứng nghiệm thu API thật.")

    if "--interactive" in sys.argv:
        print("Nhập 'exit' hoặc 'quit' để kết thúc.")
        while True:
            try:
                user_input = input("Bạn: ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\nĐã kết thúc.")
                return 0
            if not user_input or user_input.casefold() in {"exit", "quit"}:
                print("Đã kết thúc.")
                return 0
            logs = run_react_agent(user_input, provider, mcp_server)
            save_waterfall_trace(logs)

    if "--all" in sys.argv:
        passed_count, failed_cases = run_test_suite(tests, provider, mcp_server)
        print(f"\nTEST SUITE: {passed_count}/{len(tests)} PASS")
        if failed_cases:
            print(f"Failed: {', '.join(failed_cases)}")
            return 1
        return 0

    print("Usage:")
    print("  python src/app.py --all")
    print("  python src/app.py --interactive")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
