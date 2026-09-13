# 📊 BÁO CÁO THU HOẠCH NGHIỆM THU BÀI LAB 3 (BƯỚC 3 — SUBMISSION ARTIFACT)

> **Họ và Tên Học viên:** Nguyễn Tuấn Thành
> **Mã Sinh Viên / Mã Học viên:** 2A202602640
> **Chủ đề Lựa chọn:** Product Comparison Assistant — Trợ lý tìm kiếm và tạo báo cáo so sánh sản phẩm

**Phạm vi MVP:** Hệ thống làm việc với danh mục điện thoại và laptop mô phỏng. Chatbot có thể trả lời câu hỏi chung; ReAct Agent sử dụng `search_products` để tra cứu theo tên, loại hoặc ngân sách và `create_comparison_report` để tạo báo cáo từ ít nhất hai mã sản phẩm. MVP không truy cập giá bán thời gian thực, không đặt hàng, không thanh toán và không tự đưa ra kết luận mua hàng ngoài dữ liệu do tool cung cấp.

---

## 1. BẢNG CHẤM ĐIỂM AGENTIC FIT SCORING MATRIX (ĐÁNH GIÁ CHỦ ĐỀ)

| Tiêu chí Đánh giá | Mức độ (1 - 5) | Giải trình chi tiết lý do chọn điểm |
| :--- | :---: | :--- |
| **1. Multi-step Reasoning** | 4 / 5 | Yêu cầu đơn giản chỉ cần một lần tra cứu, nhưng yêu cầu tạo báo cáo theo điều kiện cần tìm sản phẩm, đọc kết quả, chọn mã phù hợp rồi mới tạo báo cáo. |
| **2. Tool Interaction** | 5 / 5 | Agent bắt buộc gọi MCP Server để lấy dữ liệu từ danh mục sản phẩm và tạo artifact báo cáo; LLM không được tự bịa giá hoặc thông số. |
| **3. Dynamic Decision** | 4 / 5 | Việc gọi tool thứ hai và các mã sản phẩm truyền vào phụ thuộc trực tiếp vào Observation do `search_products` trả về. |
| **4. Long Horizon Goal** | 3 / 5 | Agent phải giữ mục tiêu và các ràng buộc ngân sách qua nhiều bước trong một yêu cầu, nhưng MVP chưa cần memory dài hạn hoặc tự lập kế hoạch qua nhiều phiên. |
| **TỔNG ĐIỂM AGENTIC FIT** | **16 / 20** | Bài toán vượt ngưỡng 12/20 và phù hợp để minh họa ReAct đa bước, nhưng chưa cần Autonomous Agent. |

---

## 2. TRÍCH XUẤT KẾT QUẢ WATERFALL TRACE LOG (SAU KHI CHẠY TEST SUITE TRÊN API THẬT)

Lần nghiệm thu chính thức được chạy bằng `OpenAIProvider`, model `gpt-4o-mini`, bắt đầu lúc `2026-09-13T09:04:40.685466+00:00`. Dưới đây là phần rút gọn của trace `TC04`; dữ liệu đầy đủ nằm trong `docs/trace_waterfall.json`:

```json
[
  {
    "test_case_id": "TC04",
    "step": 1,
    "action_type": "TOOL_EXECUTION",
    "tool_name": "search_products",
    "arguments": {
      "category": "laptop",
      "max_price_vnd": 25000000
    },
    "observation": {
      "status": "SUCCESS",
      "count": 3,
      "product_ids": ["LP002", "LP001", "LP003"]
    },
    "llm_latency_ms": 1098.51,
    "tool_latency_ms": 0.15
  },
  {
    "test_case_id": "TC04",
    "step": 2,
    "action_type": "TOOL_EXECUTION",
    "tool_name": "create_comparison_report",
    "arguments": {
      "product_ids": ["LP002", "LP001"],
      "title": "Laptop trong ngân sách 25 triệu"
    },
    "observation": {
      "status": "SUCCESS",
      "report_id": "CMP-775E1C16"
    },
    "llm_latency_ms": 1256.11,
    "tool_latency_ms": 0.11
  },
  {
    "test_case_id": "TC04",
    "step": 3,
    "action_type": "FINAL_ANSWER",
    "llm_latency_ms": 2217.49
  }
]
```

Trace cho thấy tham số `product_ids` của bước 2 được lấy động từ Observation ở bước 1, không được ghi cứng trong prompt người dùng. Với `TC05`, Agent vẫn gọi `create_comparison_report`, nhận `INVALID_PRODUCT` cho `LP999` rồi giải thích lỗi thay vì giả lập báo cáo thành công.

---

## 3. TỔNG KẾT KẾT QUẢ NGHIỆM THU & NỘP BÀI

- **Preflight offline:** 5 / 5 test cases PASS bằng `MockOfflineProvider`; kết quả này được dùng để kiểm tra logic trước khi gọi API thật.
- [x] Đã cấu hình API Key trong `.env` cục bộ và xác nhận Agent chạy bằng `OpenAIProvider`; API key không được commit vào Git.
- **Kết quả nghiệm thu API thật:** 5 / 5 test cases PASS bằng model `gpt-4o-mini`.
- **Số lượt gọi Tool qua MCP Server chính xác:** 5 lượt, gồm 4 Observation `SUCCESS` và 1 `INVALID_PRODUCT` mong đợi ở `TC05`.
- **Waterfall trace:** 10 events; tổng LLM latency `18,859.20 ms`, tổng Tool latency `0.46 ms`.
- **Kiểm thử tự động:** 11 / 11 unit và API contract tests PASS trên Python 3.11.11.
- **Kết quả đẩy Repo nộp bài:** [x] Đã Commit và Push mã nguồn thành công lên GitHub cá nhân tại `https://github.com/Chika1357/K4A-Day03-NguyenTuanThanh-2A202602640`.

---

> ✅ **HOÀN TẤT NỘP BÀI:** Sao chép đường link GitHub Repository cá nhân của bạn và dán vào ô nộp bài trên hệ thống LMS VLearn để hoàn tất Bài Lab 3!
