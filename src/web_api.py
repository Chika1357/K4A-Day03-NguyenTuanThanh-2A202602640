"""FastAPI web layer for the Product Comparison Assistant demo."""

import time
from pathlib import Path
from typing import Any, Dict, List

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app import run_react_agent
from mcp_server import MCPProductServer
from providers import get_llm_provider
from tools import MOCK_PRODUCT_CATALOG

PROJECT_ROOT = Path(__file__).resolve().parents[1]
WEB_DIR = PROJECT_ROOT / "web"

app = FastAPI(
    title="CompareAI",
    description="Web demo for the traceable product comparison ReAct agent.",
    version="1.0.0",
)
app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")

provider = get_llm_provider()
mcp_server = MCPProductServer()


class ChatRequest(BaseModel):
    message: str = Field(min_length=2, max_length=1000)


def _collect_products(trace: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    products: Dict[str, Dict[str, Any]] = {}
    for event in trace:
        observation = event.get("observation", {})
        for product in observation.get("products", []):
            products[product["product_id"]] = product
        report = observation.get("report")
        if report:
            for product in report.get("products", []):
                products[product["product_id"]] = product
    return list(products.values())


def _collect_report(trace: List[Dict[str, Any]]) -> Dict[str, Any] | None:
    for event in reversed(trace):
        report = event.get("observation", {}).get("report")
        if report:
            return report
    return None


@app.get("/api/health")
def health() -> Dict[str, Any]:
    provider_name = provider.__class__.__name__
    return {
        "status": "online",
        "provider": provider_name,
        "model": getattr(provider, "model_name", "unknown"),
        "mode": "offline" if provider_name == "MockOfflineProvider" else "live",
        "mcp_server": mcp_server.server_name,
        "catalog_size": len(MOCK_PRODUCT_CATALOG),
    }


@app.get("/api/catalog")
def catalog() -> Dict[str, Any]:
    return {
        "data_source": "MOCK_PRODUCT_CATALOG",
        "products": list(MOCK_PRODUCT_CATALOG.values()),
    }


@app.post("/api/chat")
def chat(request: ChatRequest) -> Dict[str, Any]:
    started_at = time.perf_counter()
    trace = run_react_agent(request.message.strip(), provider, mcp_server)
    elapsed_ms = round((time.perf_counter() - started_at) * 1000, 2)

    final_event = next(
        (event for event in reversed(trace) if event.get("action_type") == "FINAL_ANSWER"),
        None,
    )
    error_event = next(
        (
            event
            for event in reversed(trace)
            if event.get("action_type")
            in {"PROVIDER_ERROR", "INVALID_LLM_RESPONSE", "REPEATED_ACTION_STOP", "MAX_ITERATIONS_REACHED"}
        ),
        None,
    )
    answer = final_event.get("output", "") if final_event else ""
    error = None
    if error_event:
        error = error_event.get("error") or error_event.get("output") or "Agent đã dừng an toàn."

    return {
        "status": "SUCCESS" if final_event else "ERROR",
        "answer": answer,
        "error": error,
        "products": _collect_products(trace),
        "report": _collect_report(trace),
        "trace": trace,
        "provider": provider.__class__.__name__,
        "model": getattr(provider, "model_name", "unknown"),
        "total_ms": elapsed_ms,
    }


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")
