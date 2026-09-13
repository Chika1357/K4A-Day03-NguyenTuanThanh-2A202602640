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

> ⚠️ **YÊU CẦU NGHIỆM THU:** Mở tệp `.env`, đặt `LLM_PROVIDER=openai` và điền `OPENAI_API_KEY` để kết nối LLM thật trước khi thực thi `python src/app.py --all`. Bài nộp chỉ dùng Mock Offline Provider sẽ không đạt điểm nghiệm thực tế.

Dán 1 đoạn trích xuất log tiêu biểu từ file `docs/trace_waterfall.json` sinh ra từ phản hồi LLM API thật:

> Chưa điền: đoạn trace tại đây phải được lấy từ lần chạy OpenAI API thật, không dùng dữ liệu mẫu hoặc Mock để thay thế.

---

## 3. TỔNG KẾT KẾT QUẢ NGHIỆM THU & NỘP BÀI

- **Preflight offline:** 5 / 5 test cases PASS bằng `MockOfflineProvider`; 5 lượt gọi tool đúng theo acceptance criteria. Kết quả này chỉ xác nhận logic nội bộ, không thay thế lần nghiệm thu bằng API thật.
- [ ] Đã điền API Key thật trong `.env` và xác nhận Agent chạy mượt mà trên OpenAI API thật.
- **Tổng số Test Cases đã chạy thành công:** ___ / 5 test cases.
- **Số lượt gọi Tool qua MCP Server chính xác:** ___ lượt.
- **Kết quả đẩy Repo nộp bài:** [ ] Đã Commit và Push mã nguồn thành công lên GitHub cá nhân.

---

> ✅ **HOÀN TẤT NỘP BÀI:** Sao chép đường link GitHub Repository cá nhân của bạn và dán vào ô nộp bài trên hệ thống LMS VLearn để hoàn tất Bài Lab 3!
