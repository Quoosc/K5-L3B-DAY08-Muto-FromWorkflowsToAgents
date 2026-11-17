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

### Shape C — Orchestrator & Bảo mật (Handoff + Trace)

- **Kiến trúc thực thi (`src/lab8/shapes/orchestrator.py`):**
  - Orchestrator đọc thông tin claim qua `get_claim_view` (chỉ lấy `claim_id`, `principal_id`, `order_id`, `ticket`; không đọc `parent_secret` hay `raw_headers_json`), gọi `MockLLM` ở bước `plan` và xử lý ngay nhánh thiếu `order_id` (`needs_info`) mà không trích xuất mã đơn từ văn bản ticket.
  - Orchestrator dựng gói giao việc qua `lab8.handoff.make_handoff` theo chuẩn `handoff.v1` và giao cho `lab8.runtime.run_readonly_investigators` chỉ với các tool đọc (`lookup_order`, `lookup_policy`, `lookup_refund_history`). Investigator không có quyền gọi tool ghi (`issue_refund`, `append_audit`).
  - Dựa trên `order_view` trả về từ investigator, orchestrator dùng code (`compute_compensation`) để tính **quote đầy đủ**, rồi gọi `durability.issue_refund(conn, claim_id, proposal, crash_at=crash_at)` khi `proposal > 0` (không bắt `InjectedCrash`, flush trace trước khi re-raise) và đóng gói `RunResult` qua `common.finish()`.
- **Cơ chế sanitize handoff & ranh giới bảo mật trace:**
  - `make_handoff` lọc cứng theo allowlist `ALLOWED_FIELDS` và `FACT_KEYS`, từ chối mọi write tool và ném `HandoffError` nếu phát hiện `CANARY_SECRET_`, `parent_secret` hoặc `raw_headers` (không dựa vào tóm tắt bằng LLM làm redaction).
  - Trace của cả 3 shape (`workflow`, `single`, `orchestrator`) chỉ ghi các event metadata đã lọc (`plan`/`claim`, `handoff` đã sanitize, `investigator`/`order` theo `ORDER_FIELDS`, `quote`, `host_outcome`/`decision`/`result`, `crash`), tuyệt đối không ghi raw claim row, raw order row (`phone`, `address`, `internal_note`, `item_name`), `parent_secret` hay `ticket` thô ra file trace, file `<run_id>*` hoặc `stdout`.
  - Mọi nhánh return sớm (`unknown_claim`, `needs_info`, `escalated`, `denied`, `failed`) và nhánh `InjectedCrash` đều ghi file JSON khớp `run_id` và có `events` là list theo `Trace contract v1`.

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

### Trần Anh Dũng — Orchestrator & Bảo mật

- Hoàn thiện `src/lab8/shapes/orchestrator.py` theo kiến trúc Orchestrator + Read-only Investigators.
- Đóng gói handoff qua `lab8.handoff.make_handoff` (`handoff.v1`), chỉ cấp read-only tools (`lookup_order`, `lookup_policy`, `lookup_refund_history`); orchestrator tự tính quote bằng `compute_compensation` và truyền quote đầy đủ + `crash_at` vào `durability.issue_refund`.
- Rà soát payload trace và viết bộ test bảo mật `src/tests/test_orchestrator_handoff_trace.py` (23 test case parametrize) kiểm tra allowlist handoff, `Trace contract v1`, `approval_claim_mismatch`, crash/resume và chống rò `CANARY_SECRET_*` / PII trên cả 3 shape (`workflow`, `single`, `orchestrator`).
- Bằng chứng: 62/62 test `student` cho `orchestrator` (248/248 toàn ma trận), `pytest -q` 84 passed, crash suite 20/20.

## 7. Hạn chế và hướng cải thiện

MockLLM không phải model sản xuất; latency là `unavailable`. Nêu thêm giới hạn của nhóm và điều kiện làm kết luận thay đổi.

...

## 8. Tài liệu tham khảo

...
