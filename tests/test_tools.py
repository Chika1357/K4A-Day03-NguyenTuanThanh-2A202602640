"""Unit tests for the product tool schemas and execution layer."""

import json
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from tools import TOOLS_SCHEMA, dispatch_tool_call


class ProductToolsTest(unittest.TestCase):
    def call_tool(self, name, arguments):
        return json.loads(dispatch_tool_call(name, arguments))

    def test_expected_tool_schemas_are_published(self):
        names = {tool["name"] for tool in TOOLS_SCHEMA}
        self.assertEqual(names, {"search_products", "create_comparison_report"})

    def test_search_respects_category_and_budget(self):
        result = self.call_tool(
            "search_products",
            {"query": "", "category": "laptop", "max_price_vnd": 25_000_000},
        )
        self.assertEqual(result["status"], "SUCCESS")
        self.assertGreaterEqual(result["count"], 2)
        self.assertTrue(all(item["category"] == "laptop" for item in result["products"]))
        self.assertTrue(all(item["price_vnd"] <= 25_000_000 for item in result["products"]))

    def test_search_returns_not_found_for_unmatched_query(self):
        result = self.call_tool("search_products", {"query": "không tồn tại"})
        self.assertEqual(result["status"], "NOT_FOUND")

    def test_comparison_report_uses_known_products(self):
        result = self.call_tool(
            "create_comparison_report",
            {"product_ids": ["LP001", "LP002"], "title": "Laptop test"},
        )
        self.assertEqual(result["status"], "SUCCESS")
        self.assertEqual(result["report"]["product_ids"], ["LP001", "LP002"])
        self.assertEqual(result["report"]["data_source"], "MOCK_PRODUCT_CATALOG")

    def test_comparison_rejects_unknown_product(self):
        result = self.call_tool(
            "create_comparison_report",
            {"product_ids": ["LP001", "LP999"], "title": "Invalid test"},
        )
        self.assertEqual(result["status"], "INVALID_PRODUCT")
        self.assertEqual(result["invalid_product_ids"], ["LP999"])


if __name__ == "__main__":
    unittest.main()
