"""
🛠️ TOOL DEFINITIONS & EXECUTION BACKEND
Mã nguồn chứa danh sách Tool Schemas (JSON Schema) và Execution Layer phục vụ cho MCP Server.
"""

import json
import hashlib
from typing import Dict, Any

# ==============================================================================
# 1. KHAI BÁO TOOL SCHEMAS CHUẨN NATIVE JSON SCHEMA (TASK 1.2)
# ==============================================================================

TOOLS_SCHEMA = [
    # Tool 1: Tra cứu dữ liệu sản phẩm
    {
        "name": "search_products",
        "description": "Tìm sản phẩm trong danh mục theo từ khóa, loại sản phẩm hoặc mức giá tối đa.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Tên hoặc từ khóa sản phẩm cần tìm; để chuỗi rỗng nếu chỉ lọc theo loại hoặc ngân sách."
                },
                "category": {
                    "type": "string",
                    "enum": ["phone", "laptop"],
                    "description": "Loại sản phẩm cần lọc."
                },
                "max_price_vnd": {
                    "type": "integer",
                    "minimum": 0,
                    "description": "Mức giá tối đa tính bằng VND."
                }
            },
            "required": ["query"]
        }
    },

    # Tool 2: Tạo artifact báo cáo so sánh từ các sản phẩm đã tra cứu
    {
        "name": "create_comparison_report",
        "description": "Tạo và lưu một báo cáo so sánh từ ít nhất hai mã sản phẩm có trong danh mục.",
        "parameters": {
            "type": "object",
            "properties": {
                "product_ids": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "minItems": 2,
                    "maxItems": 4,
                    "description": "Danh sách từ hai đến bốn mã sản phẩm cần so sánh."
                },
                "title": {
                    "type": "string",
                    "description": "Tiêu đề ngắn cho báo cáo so sánh."
                }
            },
            "required": ["product_ids", "title"]
        }
    }
]

# ==============================================================================
# 2. MÔ PHỎNG DỮ LIỆU & HÀM THỰC THI TOOL (EXECUTION LAYER)
# ==============================================================================

MOCK_PRODUCT_CATALOG = {
    "LP001": {
        "product_id": "LP001",
        "name": "Lenovo ThinkPad E14 Gen 5",
        "brand": "Lenovo",
        "category": "laptop",
        "price_vnd": 22900000,
        "cpu": "Intel Core i5",
        "ram_gb": 16,
        "storage_gb": 512,
        "display": "14 inch"
    },
    "LP002": {
        "product_id": "LP002",
        "name": "ASUS Vivobook 15",
        "brand": "ASUS",
        "category": "laptop",
        "price_vnd": 19490000,
        "cpu": "AMD Ryzen 7",
        "ram_gb": 16,
        "storage_gb": 512,
        "display": "15.6 inch"
    },
    "LP003": {
        "product_id": "LP003",
        "name": "MacBook Air M2",
        "brand": "Apple",
        "category": "laptop",
        "price_vnd": 24990000,
        "cpu": "Apple M2",
        "ram_gb": 8,
        "storage_gb": 256,
        "display": "13.6 inch"
    },
    "LP004": {
        "product_id": "LP004",
        "name": "Dell XPS 13",
        "brand": "Dell",
        "category": "laptop",
        "price_vnd": 31990000,
        "cpu": "Intel Core Ultra 7",
        "ram_gb": 16,
        "storage_gb": 512,
        "display": "13.4 inch"
    },
    "PH001": {
        "product_id": "PH001",
        "name": "Samsung Galaxy S24",
        "brand": "Samsung",
        "category": "phone",
        "price_vnd": 18990000,
        "ram_gb": 8,
        "storage_gb": 256,
        "display": "6.2 inch"
    },
    "PH002": {
        "product_id": "PH002",
        "name": "iPhone 15",
        "brand": "Apple",
        "category": "phone",
        "price_vnd": 19990000,
        "ram_gb": 6,
        "storage_gb": 128,
        "display": "6.1 inch"
    },
    "PH003": {
        "product_id": "PH003",
        "name": "Xiaomi 14T",
        "brand": "Xiaomi",
        "category": "phone",
        "price_vnd": 12990000,
        "ram_gb": 12,
        "storage_gb": 256,
        "display": "6.67 inch"
    }
}

COMPARISON_REPORTS: Dict[str, Dict[str, Any]] = {}


def _json_response(payload: Dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False)


def execute_search_products(
    query: str,
    category: str | None = None,
    max_price_vnd: int | None = None
) -> str:
    """Tìm sản phẩm trong catalog mô phỏng bằng các bộ lọc có cấu trúc."""
    if not isinstance(query, str):
        return _json_response({
            "status": "INVALID_ARGUMENTS",
            "message": "query phải là chuỗi."
        })
    if category is not None and category not in {"phone", "laptop"}:
        return _json_response({
            "status": "INVALID_ARGUMENTS",
            "message": "category phải là 'phone' hoặc 'laptop'."
        })
    if max_price_vnd is not None and (
        isinstance(max_price_vnd, bool)
        or not isinstance(max_price_vnd, int)
        or max_price_vnd < 0
    ):
        return _json_response({
            "status": "INVALID_ARGUMENTS",
            "message": "max_price_vnd phải là số nguyên không âm."
        })

    normalized_query = query.strip().casefold()
    matches = []
    for product in MOCK_PRODUCT_CATALOG.values():
        searchable_text = " ".join(
            str(value) for value in product.values()
        ).casefold()
        if normalized_query and normalized_query not in searchable_text:
            continue
        if category and product["category"] != category:
            continue
        if max_price_vnd is not None and product["price_vnd"] > max_price_vnd:
            continue
        matches.append(dict(product))

    matches.sort(key=lambda item: (item["price_vnd"], item["product_id"]))
    filters = {
        "query": query,
        "category": category,
        "max_price_vnd": max_price_vnd
    }
    if not matches:
        return _json_response({
            "status": "NOT_FOUND",
            "filters": filters,
            "message": "Không tìm thấy sản phẩm phù hợp trong catalog mô phỏng."
        })
    return _json_response({
        "status": "SUCCESS",
        "data_source": "MOCK_PRODUCT_CATALOG",
        "data_note": "Giá và thông số chỉ phục vụ bài lab, không phải dữ liệu bán hàng thời gian thực.",
        "filters": filters,
        "count": len(matches),
        "products": matches
    })


def execute_create_comparison_report(product_ids: list[str], title: str) -> str:
    """Tạo và lưu một báo cáo so sánh từ các mã sản phẩm hợp lệ."""
    if not isinstance(product_ids, list) or not 2 <= len(product_ids) <= 4:
        return _json_response({
            "status": "INVALID_ARGUMENTS",
            "message": "product_ids phải chứa từ 2 đến 4 mã sản phẩm."
        })
    if not all(isinstance(product_id, str) for product_id in product_ids):
        return _json_response({
            "status": "INVALID_ARGUMENTS",
            "message": "Mỗi product_id phải là chuỗi."
        })
    if not isinstance(title, str) or not title.strip():
        return _json_response({
            "status": "INVALID_ARGUMENTS",
            "message": "title không được để trống."
        })

    normalized_ids = [product_id.strip().upper() for product_id in product_ids]
    if len(set(normalized_ids)) != len(normalized_ids):
        return _json_response({
            "status": "INVALID_ARGUMENTS",
            "message": "Danh sách không được chứa mã sản phẩm trùng nhau."
        })

    invalid_ids = [
        product_id
        for product_id in normalized_ids
        if product_id not in MOCK_PRODUCT_CATALOG
    ]
    if invalid_ids:
        return _json_response({
            "status": "INVALID_PRODUCT",
            "invalid_product_ids": invalid_ids,
            "message": f"Không tồn tại sản phẩm: {', '.join(invalid_ids)}."
        })

    products = [dict(MOCK_PRODUCT_CATALOG[product_id]) for product_id in normalized_ids]
    prices = [product["price_vnd"] for product in products]
    cheapest = min(products, key=lambda item: item["price_vnd"])
    report_seed = json.dumps(
        {"title": title.strip(), "product_ids": normalized_ids},
        ensure_ascii=True,
        sort_keys=True
    )
    report_id = f"CMP-{hashlib.sha256(report_seed.encode('utf-8')).hexdigest()[:8].upper()}"
    report = {
        "report_id": report_id,
        "title": title.strip(),
        "product_ids": normalized_ids,
        "products": products,
        "summary": {
            "lowest_price_product_id": cheapest["product_id"],
            "lowest_price_vnd": cheapest["price_vnd"],
            "price_range_vnd": max(prices) - min(prices)
        },
        "data_source": "MOCK_PRODUCT_CATALOG",
        "data_note": "Báo cáo dùng dữ liệu mô phỏng và không phải khuyến nghị mua hàng."
    }
    COMPARISON_REPORTS[report_id] = report
    return _json_response({
        "status": "SUCCESS",
        "message": f"Đã tạo báo cáo '{report['title']}' với mã {report_id}.",
        "report": report
    })


TOOL_ROUTER = {
    "search_products": execute_search_products,
    "create_comparison_report": execute_create_comparison_report
}


def dispatch_tool_call(tool_name: str, arguments: Dict[str, Any]) -> str:
    """Kiểm tra request và chuyển tool call tới execution function tương ứng."""
    if tool_name not in TOOL_ROUTER:
        return _json_response({
            "status": "UNKNOWN_TOOL",
            "message": f"Tool '{tool_name}' không tồn tại."
        })
    if not isinstance(arguments, dict):
        return _json_response({
            "status": "INVALID_ARGUMENTS",
            "message": "arguments phải là một JSON object."
        })
    try:
        return TOOL_ROUTER[tool_name](**arguments)
    except TypeError as exc:
        return _json_response({
            "status": "INVALID_ARGUMENTS",
            "message": str(exc)
        })
    except Exception as exc:
        return _json_response({
            "status": "EXECUTION_ERROR",
            "message": str(exc)
        })
