# Báo cáo cá nhân — Trần Anh Dũng

## 1. Thông tin thành viên

- Họ tên: Trần Anh Dũng
- MSSV: 2A202604037
- Email: dungkid01@gmail.com
- GitHub: [tad-4963](https://github.com/tad-4963)

## 2. Phần việc phụ trách

- **Shape C — Orchestrator & Bảo mật (handoff + trace):**
  - Triển khai `src/lab8/shapes/orchestrator.py` theo contract `run_claim(claim_id, *, seed, store_path, crash_at=None) -> RunResult`.
  - Đóng gói handoff qua `lab8.handoff.make_handoff` (`handoff.v1`) chỉ cấp read-only tools cho investigator (`lab8.runtime.run_readonly_investigators`), không truyền `parent_secret`, `raw_headers` hay full claim row.
  - Để code/host quyết định quote (`compute_compensation`) và ghi ledger (`durability.issue_refund`), truyền `crash_at` và không bắt `InjectedCrash`.
  - Rà soát payload trace và viết test bổ sung về handoff allowlist, secret/PII leakage và `Trace contract v1`.

## 3. Đóng góp cụ thể

- Triển khai hoàn chỉnh Shape C trong `src/lab8/shapes/orchestrator.py`:
  - Đọc claim qua `get_claim_view` (tránh `SELECT *` làm lộ `parent_secret` / `raw_headers_json`), đóng kết nối SQLite trong `finally`.
  - Xử lý đủ mọi nhánh return sớm có ghi `Trace` đầy đủ: `unknown_claim` (`failed`), thiếu `order_id` (`needs_info`, không tự lấy mã đơn từ ticket), không thấy đơn / sai principal (`escalated`).
  - Dựng handoff qua `make_handoff` với 3 read-only tools (`lookup_order`, `lookup_policy`, `lookup_refund_history`), chạy `run_readonly_investigators`, sau đó orchestrator tự tính quote bằng `compute_compensation`.
  - Truyền **quote đầy đủ** và `crash_at` vào `durability.issue_refund` khi `proposal > 0` (ghi event `crash` và `trace.write()` trước khi re-raise `InjectedCrash`); không gọi `issue_refund` khi `proposal <= 0`; trả kết quả qua `lab8.shapes.common.finish()`.
- Tạo bộ test bổ sung `src/tests/test_orchestrator_handoff_trace.py` (23 test case parametrize):
  - Kiểm tra `make_handoff` lọc field ngoài allowlist, chặn canary trong `facts` và chặn write tool (`append_audit`).
  - Kiểm tra trace `handoff` của `orchestrator` đúng `handoff.v1` và chỉ dùng `READONLY_TOOLS`.
  - Quét `artifact_blob` và `stdout`/`stderr` trên cả **3 shape** (`orchestrator`, `single`, `workflow`) ở đủ 6 nhánh return (`resolved`, `denied` quote=0, `needs_info`, `escalated`, `denied` approval, `failed`) để đảm bảo không rò `CANARY_SECRET_*`, `Bearer `, SĐT, địa chỉ, ghi chú nội bộ hay tên hàng.
  - Kiểm tra `approval_claim_mismatch` (audit `policy_denied`, 0 dòng ledger) và crash/resume (`before_effect`, `after_effect_before_checkpoint`).

## 4. Bằng chứng

- File triển khai: `src/lab8/shapes/orchestrator.py`
- File test bổ sung: `src/tests/test_orchestrator_handoff_trace.py`
- Kết quả tự kiểm tra trên máy (chạy trong `src/`):
  - `python -m pytest -q -m student -o addopts=`: **248 passed, 84 deselected** (toàn bộ 4 shape `workflow`, `single`, `orchestrator`, `swarm` đạt 62/62).
  - `python -m pytest -q`: **84 passed, 248 deselected** (gồm test host + `test_workflow.py` + 23 test case trong `test_orchestrator_handoff_trace.py` rà cả 3 shape).
  - `python -m lab8.crash_test --count 20 --out reports/crash.json`: **`crash_safety 20/20`**
  - Benchmark đối chứng `single,orchestrator,swarm` (14 public claims × 5 seeds `11,22,33,44,55`): `orchestrator` đạt pass rate `1.000`, pass^5 `1.000`, seed variance `0.000000`, cost/success `57.19` VND (mô phỏng), mean steps `4.71`.
- Commit hash chính (Shape C + test + báo cáo): `381881f` (cập nhật đồng bộ thêm test rà cả 3 shape và mô tả bảo mật ở commit tiếp theo).

## 5. Công cụ AI đã dùng

- Sử dụng trợ lý AI trong IDE để đọc và đối chiếu tài liệu nghiệp vụ/contract (`docs/business_rules.md`, `docs/contracts.md`, `handoff.py`, `runtime.py`, `durability.py`), hỗ trợ viết `orchestrator.py` và bộ test `test_orchestrator_handoff_trace.py`.
- Tự kiểm chứng toàn bộ bằng `pytest -q`, ma trận `student`, `lab8.crash_test`, `lab8.benchmark`, `lab8.demo.buggy_workflow`, và kiểm tra trực tiếp nội dung các file JSON trong `src/traces/`.

## 6. Tự đánh giá

- Đã hoàn thành đầy đủ phần cài đặt Shape C (`orchestrator.py`), kiểm thử bảo mật handoff/trace cho cả 3 shape (`workflow`, `single`, `orchestrator`) và phần mô tả bảo mật trong báo cáo nhóm/ADR.
