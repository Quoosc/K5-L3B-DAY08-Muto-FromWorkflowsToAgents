# Báo cáo nhóm — Lab 8 LogiX-VN

Tối đa 5 trang ngoài phụ lục. Số liệu lấy từ file trong `src/reports/`, không chép tay từ terminal.

## 1. Thông tin nhóm

- Tên nhóm: Muto
- Thành viên: xem `TEAM.md`
- Commit chốt (trùng `report/team/decision_adr.md`): 403cca7 (code và bằng chứng đánh giá public)

## 2. Mục tiêu và cách tiếp cận

Cùng xử lý claim theo bốn shape, giữ tiền và approval trong code/host. Hoàng Minh phụ trách workflow và tích hợp; Phạm Trấn Quốc phụ trách single; Trần Anh Dũng phụ trách orchestrator/handoff; Nguyễn Quốc Quang Anh phụ trách kiểm thử host và đánh giá. Người 4 kiểm thử host trước, sau đó chạy toàn bộ ma trận và benchmark khi nhận đủ ba shape.

## 3. Giải pháp

Workflow chạy các bước Python cố định; single dùng run_react tối đa 8 bước với worker=True. Cả hai lấy claim view, kiểm order theo principal, quote bằng compute_compensation rồi truyền quote đầy đủ cho host. Single gọi MockLLM nhưng không dùng kết quả để chọn tool: decide hiện là các nhánh Python. Ba shape lấy effect/audit từ ledger qua finish và để crash truyền ra ngoài.

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

| Shape | Pass rate | Pass^5 | Seed min–max | Variance | Cost/success VND | Mean/p95 steps |
| --- | --- | --- | --- | --- | --- | --- |
| workflow | 1.000000 | 1.000000 | 1.000000–1.000000 | 0.000000000 | 34.285714 | 5.071429/6 |
| single | 1.000000 | 1.000000 | 1.000000–1.000000 | 0.000000000 | 30.087143 | 2.000000/2 |
| orchestrator | 1.000000 | 1.000000 | 1.000000–1.000000 | 0.000000000 | 57.190000 | 4.714286/5 |
| swarm | 0.985714 | 0.928571 | 0.928571–1.000000 | 0.000816327 | 49.566957 | 2.800000/3 |

Nguồn: `src/reports/benchmark.json`, 14 claim × 5 seed × 4 shape. Host gate 91 pass; student matrix 248 pass; crash suite 20/20. Swarm fail duy nhất C-002 seed 55. Hidden chưa được phát/chấm. Chi tiết giới hạn và lệnh tái lập: `report/team/member4_evaluation.md`.

Quyết định kiến trúc và lý do: xem `report/team/decision_adr.md`. Phiếu nghiên cứu và ablation: xem `report/team/research_card.md`.

## 5. Khó khăn và cách xử lý

Môi trường người 4 hiện dùng Python 3.14.10/pytest 9.2.0, ngoài dải phiên bản lab. Các lệnh kiểm thử public xanh nhưng cần chạy lại trên Python 3.11–3.13 và pytest <9 trước khi nộp. Chưa có student_drop nên không chạy self-check hidden.

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

### Nguyễn Quốc Quang Anh — Ledger + evaluation

Commit `403cca7`: thêm 7 ca host edge, chạy 91 test host và 248 test student, sinh benchmark bốn shape và crash report 20/20. Tổng hợp số liệu, rà giới hạn, chuẩn bị ADR. Báo cáo cá nhân: `2A202604120_NguyenQuocQuangAnh.md`.

## 7. Hạn chế và hướng cải thiện

MockLLM không phải model sản xuất; latency unavailable. Workflow tính tool cost cho issue_refund còn các shape khác không tính lời gọi ghi; trace có mức chi tiết khác nhau, nên steps và cost cần diễn giải theo cách đếm hiện tại. Chưa cô lập topology bằng ablation; research card chưa hoàn tất. Đề xuất workflow cần được nhóm xác nhận và xem lại sau hidden/task mới.

## 8. Tài liệu tham khảo

`README.md`, `RULES.md`, `RUBRIC.md`, `docs/business_rules.md`, `docs/contracts.md`, `docs/metrics.md`, source ba shape và hai file report do CLI lab sinh. Chưa bổ sung nguồn nghiên cứu bên ngoài cho research card.
