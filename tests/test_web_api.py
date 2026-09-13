"""HTTP contract tests for the local demo web application."""

import sys
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import web_api
from providers import MockOfflineProvider


class WebApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original_provider = web_api.provider
        web_api.provider = MockOfflineProvider()
        cls.client = TestClient(web_api.app)

    @classmethod
    def tearDownClass(cls):
        web_api.provider = cls.original_provider

    def test_home_page_is_served(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("CompareAI", response.text)

    def test_health_exposes_non_secret_runtime_metadata(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "online")
        self.assertEqual(payload["catalog_size"], 7)
        self.assertNotIn("api_key", payload)

    def test_chat_returns_answer_products_and_trace(self):
        response = self.client.post(
            "/api/chat",
            json={"message": "Tìm giúp tôi các laptop có giá không quá 25 triệu đồng."},
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "SUCCESS")
        self.assertGreaterEqual(len(payload["products"]), 2)
        self.assertTrue(any(event["action_type"] == "TOOL_EXECUTION" for event in payload["trace"]))

    def test_chat_rejects_empty_message(self):
        response = self.client.post("/api/chat", json={"message": ""})
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
