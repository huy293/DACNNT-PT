---
name: qa-7-layers
description: Quy trình kiểm thử chất lượng 7 tầng dành cho QA Testing Engineer Agent (Unit, Integration, Business Flow, E2E Playwright, Performance, Security Pentest, Reliability Recovery)
---

# SKILL: QA Testing Engineer — 7 Tầng Kiểm Thử Bắt Buộc

## 1. Khi Nào Kích Hoạt Kỹ Năng Này?
Kích hoạt ngay sau khi Dev Agent hoàn thành một tính năng hoặc một Sprint trong `docs/ROADMAP.md`, trước khi cho phép tạo Pull Request hoặc deploy.

## 2. Ma Trận 7 Tầng Kiểm Thử Bắt Buộc
Agent đóng vai **QA Testing Engineer** độc lập (cấm tự sửa code ứng dụng để ép test pass) và thực thi lần lượt 7 tầng:
1. **Tầng 1 — Source / Unit Test:** Cắm trực tiếp vào từng hàm/method để kiểm tra đầu vào/đầu ra, `null`/`undefined`, mảng rỗng `[]`, biên số học theo chuẩn Google Testing.
2. **Tầng 2 — Integration Test:** Kiểm tra kết nối thực tế giữa Frontend $\leftrightarrow$ Backend API $\leftrightarrow$ PostgreSQL $\leftrightarrow$ Redis Cache.
3. **Tầng 3 — Business Flow Test:** Đối chiếu từng dòng với `docs/product/BUSINESS_FLOW.md` (ví dụ: nhập sai mật khẩu quá 5 lần có khóa tài khoản không, phân quyền RBAC có chặn đúng role không, thanh toán trùng lặp có bị chặn không).
4. **Tầng 4 — End-to-End (E2E) Test:** Dùng Playwright giả lập hành trình người dùng thật từ đầu đến cuối trên cả Mobile (`375x812`) và Desktop (`1440x900`).
5. **Tầng 5 — Performance & Load Test:** Kiểm tra độ trễ (Latency p95/p99) và khả năng chịu tải khi nhiều người dùng truy cập đồng thời (k6 / autocannon).
6. **Tầng 6 — Security & Pentest:** Kiểm tra 7 bước bảo mật (Path Traversal, SQL Injection, XSS, SSRF, RCE, lộ token, quét CVE thư viện bên thứ 3) và ghi vào `docs/qa/PENTEST_REPORT.md`.
7. **Tầng 7 — Reliability & Recovery Test:** Kiểm tra khả năng tự phục hồi (Self-healing) khi DB/Redis ngắt kết nối đột ngột và kiểm chứng cơ chế backup (RDB/AOF/CDC).

## 3. Báo Cáo Đầu Ra
Cập nhật toàn bộ kết quả Pass/Fail và bằng chứng log vào `docs/qa/QA_TESTING.md`.
