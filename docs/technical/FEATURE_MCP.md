# MCP FEATURE & SECURITY SPECIFICATION (`FEATURE_MCP.md`)

> **Vai trò của tệp này:** Đây là khuôn mẫu đặc tả các tính năng và phạm vi quyền hạn mà hệ thống cho phép **MCP Server (`mcp/`)** cung cấp cho các AI Agent bên ngoài (Claude Desktop, ChatGPT, nội bộ).
> - AI đọc tệp này để sinh code cho thư mục `mcp/` tuân thủ nghiêm ngặt **5 lớp bảo mật**.

---

## 1. Năm Nguyên Tắc Bảo Mật Bắt Buộc Của MCP Server

1. **Xác thực bằng API Key có vòng đời (`API Key Authentication`):**
   - Mỗi khóa API tạo ra chỉ hiển thị **đúng 1 lần duy nhất**, bắt buộc gắn **Ngày hết hạn (`expires_at`)**, giới hạn thiết bị và định danh người tạo.
2. **Quản lý phiên & Giới hạn tần suất (`Session & Rate Limiting`):**
   - Giới hạn số lượng request (ví dụ: tối đa `100 requests / thiết bị / phút`) để ngăn chặn AI Agent bị kẹt vòng lặp spam làm quá tải hệ thống.
3. **Phân quyền theo Phạm vi (`RBAC / Scope Authorization`):**
   - Tách biệt hoàn toàn nhóm quyền **Chỉ đọc (`read:*`)** và nhóm quyền **Ghi (`write:*`)**. Mặc định mọi API Key cấp cho AI chỉ bật quyền `read:*`.
4. **Sổ đăng ký Công cụ & Phản xạ JEV (`Tool Registry + JEV Middleware`):**
   - Chỉ những công cụ được liệt kê trong Bảng 2 dưới đây mới được phép đăng ký vào MCP Server.
   - Mọi công cụ thuộc nhóm `write:*` bắt buộc đi qua bộ chấm điểm phản xạ **JEV** (`Score 0.00–0.30`: Cho phép, `0.31–0.70`: Hỏi xác nhận người dùng, `0.71–1.00`: Chặn đứng).
5. **Kết nối qua API Client giới hạn (`Scoped API Client`):**
   - MCP Server **CẤM** kết nối trực tiếp vào Database Production; bắt buộc gọi qua Backend API bằng Scoped Token và ghi nhận đầy đủ vào Audit Log.

---

## 2. Danh Mục Công Cụ Được Phê Duyệt Cho MCP (`Approved Tool Registry`)

| Tên Tool (`Tool Name`) | Phạm vi quyền (`Scope`) | Điểm rủi ro JEV | Mô tả chức năng | Trạng thái |
| :--- | :--- | :---: | :--- | :---: |
| `get_students_list` | `read:students` | `0.10 (Allow)` | Tra cứu danh sách học viên và tiến độ học tập. | `ENABLED` |
| `get_courses_catalog` | `read:courses` | `0.05 (Allow)` | Đọc danh mục khóa học, lộ trình và học phí công khai. | `ENABLED` |
| `get_teaching_schedule` | `read:schedule` | `0.10 (Allow)` | Xem lịch dạy và lịch học trong ngày/tuần. | `ENABLED` |
| `get_tuition_status` | `read:tuition` | `0.20 (Allow)` | Kiểm tra trạng thái đóng học phí của học viên. | `ENABLED` |
| `get_summary_analytics` | `read:analytics` | `0.20 (Allow)` | Tổng hợp báo cáo số lượng học viên và buổi học. | `ENABLED` |
| `create_schedule_note` | `write:schedule_note` | `0.45 (Ask User)` | Thêm ghi chú chuẩn bị bài học cho buổi dạy (cần xác nhận). | `OPTIONAL` |
| `delete_database_record` | `admin:destructive` | `1.00 (Block)` | Xóa dữ liệu hệ thống — **CẤM TUYỆT ĐỐI TRÊN MCP**. | `BLOCKED` |
