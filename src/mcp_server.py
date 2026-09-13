"""MCP server facade for the product-comparison tools."""

import json
import sys
from typing import Any, Dict, List

from tools import TOOLS_SCHEMA, dispatch_tool_call

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


class MCPProductServer:
    """Expose the local tool registry through a JSON-RPC-like response envelope."""

    def __init__(self, server_name: str = "product-comparison-mcp-server"):
        self.server_name = server_name
        self.version = "2026.1.0"

    def list_tools(self) -> List[Dict[str, Any]]:
        """Return the native JSON schemas advertised to the LLM."""
        return TOOLS_SCHEMA

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatch a tool call and wrap its structured result as JSON-RPC 2.0."""
        raw_result = dispatch_tool_call(tool_name, arguments)
        try:
            content = json.loads(raw_result)
        except json.JSONDecodeError as exc:
            content = {
                "status": "EXECUTION_ERROR",
                "message": f"Tool returned invalid JSON: {exc}",
            }

        return {
            "jsonrpc": "2.0",
            "server": self.server_name,
            "tool": tool_name,
            "result": content,
        }


if __name__ == "__main__":
    server = MCPProductServer()
    tools = server.list_tools()
    tool_names = [tool.get("name") for tool in tools]

    print("MCP SERVER SELF-CHECK")
    print(f"Server: {server.server_name} (version {server.version})")
    print(f"Tools: {', '.join(tool_names)}")

    expected_tools = {"search_products", "create_comparison_report"}
    schemas_valid = (
        set(tool_names) == expected_tools
        and all(tool.get("parameters", {}).get("properties") for tool in tools)
    )
    print(f"Tool schemas: {'PASS' if schemas_valid else 'FAIL'}")

    test_result = server.call_tool(
        "search_products",
        {"query": "", "category": "laptop", "max_price_vnd": 25_000_000},
    )
    dispatch_valid = test_result.get("result", {}).get("status") == "SUCCESS"
    print(f"JSON-RPC dispatch: {'PASS' if dispatch_valid else 'FAIL'}")
    print(json.dumps(test_result, ensure_ascii=False, indent=2))
