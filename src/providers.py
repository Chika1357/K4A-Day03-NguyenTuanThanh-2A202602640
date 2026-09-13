"""LLM adapters for OpenAI, Gemini, and deterministic offline testing."""

import json
import os
import re
from typing import Any, Dict, List

from dotenv import load_dotenv

load_dotenv()


class BaseLLMProvider:
    """Common interface for providers with native tool calling."""

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        raise NotImplementedError

    def generate_with_tools(
        self,
        prompt: str,
        tools_schema: List[Dict[str, Any]],
        system_prompt: str = "",
    ) -> Dict[str, Any]:
        raise NotImplementedError


class MockOfflineProvider(BaseLLMProvider):
    """Deterministic provider used to validate orchestration without API cost."""

    def __init__(self):
        self.model_name = "offline-mock-product-agent"

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        return (
            "Tôi có thể hướng dẫn chọn tiêu chí so sánh. "
            "Để lấy dữ liệu sản phẩm cụ thể, cần dùng Agent có công cụ."
        )

    def generate_with_tools(
        self,
        prompt: str,
        tools_schema: List[Dict[str, Any]],
        system_prompt: str = "",
    ) -> Dict[str, Any]:
        del tools_schema, system_prompt
        prompt_lower = prompt.casefold()
        product_ids = list(dict.fromkeys(re.findall(r"\b(?:LP|PH)\d{3}\b", prompt.upper())))
        has_history = "lịch sử react:" in prompt_lower

        if has_history and '"status": "invalid_product"' in prompt_lower:
            invalid_id = "LP999" if "LP999" in product_ids else "mã đã yêu cầu"
            return {
                "type": "text",
                "content": (
                    f"Không thể tạo báo cáo vì {invalid_id} không tồn tại trong catalog mô phỏng. "
                    "Tôi không tự tạo dữ liệu thay thế."
                ),
                "thought": "Tool đã xác nhận mã sản phẩm không hợp lệ; cần dừng và báo đúng lỗi.",
            }

        if has_history and '"status": "not_found"' in prompt_lower:
            return {
                "type": "text",
                "content": "Không tìm thấy sản phẩm phù hợp trong catalog mô phỏng.",
                "thought": "Không có dữ liệu phù hợp để thực hiện bước tiếp theo.",
            }

        if has_history and '"report_id"' in prompt_lower:
            report_match = re.search(r'"report_id":\s*"([^"]+)"', prompt, re.IGNORECASE)
            report_id = report_match.group(1) if report_match else "đã tạo"
            return {
                "type": "text",
                "content": (
                    f"Đã tạo báo cáo so sánh {report_id} từ dữ liệu catalog mô phỏng. "
                    "Kết quả không phải giá bán thời gian thực hay khuyến nghị mua hàng."
                ),
                "thought": "Báo cáo đã được tạo thành công; có thể trả lời và kết thúc.",
            }

        if has_history and '"products"' in prompt_lower:
            if "tạo báo cáo" in prompt_lower:
                selected_ids = [item for item in product_ids if item != "LP999"][:2]
                return {
                    "type": "tool_call",
                    "tool_name": "create_comparison_report",
                    "arguments": {
                        "product_ids": selected_ids,
                        "title": "Laptop trong ngân sách 25 triệu",
                    },
                    "thought": "Đã có kết quả tìm kiếm; dùng hai product_id đầu tiên để tạo báo cáo.",
                }
            return {
                "type": "text",
                "content": (
                    "Đã tìm thấy các sản phẩm phù hợp trong catalog mô phỏng. "
                    "Giá và thông số không phải dữ liệu bán hàng thời gian thực."
                ),
                "thought": "Đã có kết quả tìm kiếm và yêu cầu không cần thêm hành động.",
            }

        if "tìm" in prompt_lower and "laptop" in prompt_lower:
            return {
                "type": "tool_call",
                "tool_name": "search_products",
                "arguments": {
                    "query": "",
                    "category": "laptop",
                    "max_price_vnd": 25_000_000,
                },
                "thought": "Cần tra catalog để lọc laptop theo ngân sách 25 triệu đồng.",
            }

        if "tạo báo cáo" in prompt_lower and len(product_ids) >= 2:
            title_match = re.search(r"tiêu đề\s+['\"]([^'\"]+)['\"]", prompt, re.IGNORECASE)
            title = title_match.group(1) if title_match else "Báo cáo so sánh sản phẩm"
            return {
                "type": "tool_call",
                "tool_name": "create_comparison_report",
                "arguments": {"product_ids": product_ids[:2], "title": title},
                "thought": "Yêu cầu đã cung cấp đủ hai mã sản phẩm để tạo báo cáo.",
            }

        return {
            "type": "text",
            "content": (
                "Tôi có thể tìm điện thoại hoặc laptop trong catalog mô phỏng theo từ khóa, "
                "loại và ngân sách, rồi tạo báo cáo so sánh từ 2-4 mã sản phẩm hợp lệ."
            ),
            "thought": "Đây là câu hỏi chung về phạm vi hỗ trợ nên không cần gọi công cụ.",
        }


class GeminiProvider(BaseLLMProvider):
    """Google Gemini adapter with native function calling."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "gemini-2.5-flash"

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        try:
            from google import genai

            client = genai.Client(api_key=self.api_key)
            contents = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            response = client.models.generate_content(model=self.model_name, contents=contents)
            return response.text or ""
        except Exception as exc:
            return f"[Gemini API error] {exc}"

    def generate_with_tools(
        self,
        prompt: str,
        tools_schema: List[Dict[str, Any]],
        system_prompt: str = "",
    ) -> Dict[str, Any]:
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self.api_key)
            declarations = [
                {
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "parameters": tool["parameters"],
                }
                for tool in tools_schema
                if tool.get("name") and tool.get("parameters")
            ]
            config = types.GenerateContentConfig(
                system_instruction=system_prompt or None,
                tools=[{"function_declarations": declarations}] if declarations else None,
                temperature=0.2,
            )
            response = client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config,
            )
            if response.function_calls:
                call = response.function_calls[0]
                arguments = dict(call.args) if call.args else {}
                return {
                    "type": "tool_call",
                    "tool_name": call.name,
                    "arguments": arguments,
                    "thought": f"Gemini chọn công cụ {call.name}.",
                }
            return {
                "type": "text",
                "content": response.text or "",
                "thought": "Gemini chọn trả lời trực tiếp.",
            }
        except Exception as exc:
            return {
                "type": "error",
                "content": f"Gemini API error: {exc}",
                "thought": "Không thể nhận phản hồi hợp lệ từ Gemini API.",
            }


class OpenAIProvider(BaseLLMProvider):
    """OpenAI adapter with native function calling."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "gpt-4o-mini"

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        try:
            from openai import OpenAI

            client = OpenAI(api_key=self.api_key)
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            response = client.chat.completions.create(model=self.model_name, messages=messages)
            return response.choices[0].message.content or ""
        except Exception as exc:
            return f"[OpenAI API error] {exc}"

    def generate_with_tools(
        self,
        prompt: str,
        tools_schema: List[Dict[str, Any]],
        system_prompt: str = "",
    ) -> Dict[str, Any]:
        try:
            from openai import OpenAI

            client = OpenAI(api_key=self.api_key)
            tools = [
                {
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool.get("description", ""),
                        "parameters": tool.get("parameters", {}),
                    },
                }
                for tool in tools_schema
                if tool.get("name")
            ]
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            response = client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                tools=tools or None,
                tool_choice="auto" if tools else None,
                temperature=0.2,
            )
            message = response.choices[0].message
            if message.tool_calls:
                call = message.tool_calls[0]
                arguments = json.loads(call.function.arguments or "{}")
                return {
                    "type": "tool_call",
                    "tool_name": call.function.name,
                    "arguments": arguments,
                    "thought": f"OpenAI chọn công cụ {call.function.name}.",
                }
            return {
                "type": "text",
                "content": message.content or "",
                "thought": "OpenAI chọn trả lời trực tiếp.",
            }
        except Exception as exc:
            return {
                "type": "error",
                "content": f"OpenAI API error: {exc}",
                "thought": "Không thể nhận phản hồi hợp lệ từ OpenAI API.",
            }


def get_llm_provider() -> BaseLLMProvider:
    """Create the configured provider; use mock only when explicitly selected or keyless."""
    provider_type = os.getenv("LLM_PROVIDER", "openai").strip().lower()
    if provider_type == "openai":
        key = os.getenv("OPENAI_API_KEY")
        return OpenAIProvider() if key and key != "your_openai_api_key_here" else MockOfflineProvider()
    if provider_type == "gemini":
        key = os.getenv("GEMINI_API_KEY")
        return GeminiProvider() if key and key != "your_gemini_api_key_here" else MockOfflineProvider()
    if provider_type == "mock":
        return MockOfflineProvider()
    raise ValueError("LLM_PROVIDER phải là 'openai', 'gemini' hoặc 'mock'.")
