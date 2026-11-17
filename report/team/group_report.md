# Báo cáo nhóm — Lab 8 LogiX-VN

Tối đa 5 trang ngoài phụ lục. Số liệu lấy từ file trong `src/reports/`, không chép tay từ terminal.

## 1. Thông tin nhóm

- Tên nhóm:
- Thành viên: xem `TEAM.md`
- Commit chốt (trùng `report/team/decision_adr.md`):

## 2. Mục tiêu và cách tiếp cận

Nhóm hiểu bài toán thế nào, chia việc ra sao, thứ tự làm bốn shape.

...

## 3. Giải pháp

Mô tả ba shape nhóm viết (workflow, single, orchestrator): mỗi shape đọc gì, quyết định gì, gọi host ra sao. Chỉ rõ ranh giới code / model (tham khảo [docs/architecture.md](../../docs/architecture.md)), cách handoff được sanitize và trace ghi những event nào.

...

## 4. Kết quả

Bảng so sánh 4 shape trên bộ public (từ `src/reports/benchmark.json`): pass rate, pass^5, seed min–max, variance, cost/success, mean/p95 steps. Kèm crash safety (`src/reports/crash.json`) và, nếu có, kết quả tự kiểm trên `student_drop/`.

...

Quyết định kiến trúc và lý do: xem `report/team/decision_adr.md`. Phiếu nghiên cứu và ablation: xem `report/team/research_card.md`.

## 5. Khó khăn và cách xử lý

Lỗi gặp phải (kèm lệnh, output hoặc ảnh chụp) và cách nhóm xử lý.

...

## 6. Tổng hợp đóng góp

Chi tiết đóng góp của từng thành viên nằm trong `TEAM.md` (bảng đóng góp) và báo cáo cá nhân `report/team/MSSV_HoTen.md`.

### Phạm Trấn Quốc — Single Agent

- Hoàn thiện `src/lab8/shapes/single.py` với ReAct loop tối đa 8 bước.
- Agent chỉ dùng read-only tools: `get_claim_view`, `lookup_order`,
  `compute_compensation`.
- Host là nơi duy nhất thực hiện refund, approval và per-order cap.
- Quote đầy đủ được chuyển tới `durability.issue_refund`, không tự trừ history.
- Trace chỉ ghi payload đã lọc, không ghi raw claim/order row hoặc secret.
- Xử lý `needs_info`, `escalated`, `denied`, `failed` và `resolved`.
- Bằng chứng: 62/62 test Single Agent, host suite 54 pass, crash 20/20.
- Benchmark riêng Shape B: pass rate 1.000, pass^5 1.000, variance 0.000000.

Chi tiết implementation và tự đánh giá nằm trong báo cáo cá nhân của Phạm
Trấn Quốc. Các số liệu benchmark bốn shape, ADR và research card vẫn là
trách nhiệm chung của nhóm.

## 7. Hạn chế và hướng cải thiện

MockLLM không phải model sản xuất; latency là `unavailable`. Nêu thêm giới hạn của nhóm và điều kiện làm kết luận thay đổi.

...

## 8. Tài liệu tham khảo

...
