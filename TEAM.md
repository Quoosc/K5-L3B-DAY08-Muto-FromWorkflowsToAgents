# Team

## Thông tin nhóm

* Tên nhóm: Muto
* Lớp: L3B
* Repo nhóm: `K5-L3B-DAY08-Muto-FromWorkflowsToAgents`
* URL repo, nhánh nộp, commit chốt: https://github.com/Quoosc/K5-L3B-DAY08-Muto-FromWorkflowsToAgents (nhánh `main`; commit chốt sẽ cập nhật sau khi commit/push)

## Thành viên

|STT|Họ tên|MSSV|Email|GitHub|Vai trò|
|-:|-|-|-|-|-|
|1|Hoàng Minh|2A202604103|[minh03forwork@gmail.com](mailto:minh03forwork@gmail.com)|[WorkOfMinh](https://github.com/WorkOfMinh)|Workflow + tích hợp|
|2|Phạm Trấn Quốc|2A202604113|[phamquoc896@gmail.com](mailto:phamquoc896@gmail.com)|[Quoosc](https://github.com/Quoosc)|Single agent|
|3|Trần Anh Dũng|2A202604037|[dungkid01@gmail.com](mailto:dungkid01@gmail.com)|[tad-4963](https://github.com/tad-4963)|Orchestrator + handoff|
|4|Nguyễn Quốc Quang Anh|2A202604120|[nguyenquocquanganh28@gmail.com](mailto:nguyenquocquanganh28@gmail.com)|[QuangAnh28](https://github.com/QuangAnh28)|Ledger + evaluation|

Gợi ý chia vai:

* Nhóm 6 người: integration; workflow; single agent; orchestrator; ledger/policy/crash; eval/report.
* Nhóm 4 người: workflow + integration; single; orchestrator + handoff; ledger + evaluation.

## Bảng đóng góp

`python -m lab8.check_submission` đọc bảng này bằng máy: giữ nguyên tiêu đề `## Bảng đóng góp` và các cột. Mỗi người một dòng: commit có nội dung và ít nhất một test đã thêm hoặc sửa.

| Người | Vai | Commit | Test đã thêm hoặc sửa |
| --- | --- | --- | --- |
| Hoàng Minh | Workflow + tích hợp | `ca4e254`, `1e54dd0` | `src/tests/test_workflow.py` (7 ca); student workflow 62 passed |
| Phạm Trấn Quốc | Single agent | `5d118a5`, `f974e1e` | `src/tests/test_single_agent.py` (2 tests); Single Agent 62 passed |
| Trần Anh Dũng | Orchestrator + handoff | `381881f`, `ad12a74` | `src/tests/test_orchestrator_handoff_trace.py` (23 ca) |
| Nguyễn Quốc Quang Anh | Ledger + evaluation + bonus B2 | `403cca7`, `3b122cb` | `src/tests/test_member4_host_edges.py` (7 ca); `src/tests/test_bonus_mast.py` (3 tests pass); benchmark/crash rerun |

## Cá nhân

Mỗi thành viên đồng thời tạo một báo cáo riêng trong `report/` theo dạng:

```text
report/team/MSSV_HoTen.md
```

Ví dụ: `report/team/20241234_NguyenVanAn.md`.

Sao chép mục dưới đây cho từng thành viên.

## MSSV_HoTen

### Phần việc phụ trách

*

### Đóng góp cụ thể

*

### Bằng chứng

*

## 2A202604113_PhamTranQuoc

### Phần việc phụ trách

* Shape B — Single Agent.
* Triển khai vòng ReAct tối đa 8 bước trong `src/lab8/shapes/single.py`.
* Giữ model ở ranh giới read-only; code/host chịu trách nhiệm quote, approval và refund.
* Bảo đảm idempotency, per-order cap, crash/resume và trace không lộ secret/PII.

### Đóng góp cụ thể

* Thay stub Single Agent bằng implementation hoàn chỉnh.
* Kết nối `run_react`, `Budget`, `Trace`, `finish` và `durability.issue_refund`.
* Xử lý chuỗi `get_claim_view` → `lookup_order` → `compute_compensation`.
* Truyền quote đầy đủ cho host và chuyển tiếp `crash_at` mà không bắt `InjectedCrash`.
* Giữ giới hạn step và đếm model/tool calls trong `Budget`.
* Xử lý đầy đủ các trạng thái của `RunResult`.
* Không lấy số ngày trễ từ ticket để quyết định compensation.
* Không tự trừ refund history trước khi gọi host.
* Giữ trace ở mức payload allowlist, không ghi raw claim/order row.

### Bằng chứng

* Báo cáo cá nhân: `report/team/2A202604113_PhamTranQuoc.md`.
* 62 test Single Agent pass.
* Host suite: 93 passed.
* Crash safety: 20/20.
* Public benchmark Single Agent: pass rate 1.000, pass^5 1.000.
* Host suite: 93 passed, 248 deselected.
* Syntax check bằng `py_compile`: đạt.
* `git diff --check`: đạt.
* Commit triển khai và báo cáo: `5d118a5`.
* Commit test bổ sung: `f974e1e`.
* Test bổ sung: `src/tests/test_single_agent.py`.
* Test bổ sung pass: 2 passed.
* Các seed benchmark: 11, 22, 33, 44, 55.
* Phạm vi kết luận: chỉ Shape B.

### Quy trình thực hiện

* Đọc `README.md`, `CHECKPOINTS.md`, `docs/contracts.md` và `docs/business_rules.md`.
* Đối chiếu `runtime.py`, `tools.py`, `durability.py`, `trace.py` và shape swarm reference.
* Tạo môi trường Python 3.12 trong `src/.venv`.
* Cài dependencies từ `src/requirements.txt`.
* Chạy smoke, student matrix, host suite, crash suite và benchmark public.
* Đối chiếu kết quả với contract trước khi ghi vào báo cáo cá nhân.


## 2A202604103_HoangMinh

### Phần việc phụ trách

* Shape A (`src/lab8/shapes/workflow.py`): chuỗi bước Python cố định; tiền do code tính, host kiểm duyệt và ghi refund.
* Test cá nhân: `src/tests/test_workflow.py`; benchmark riêng Shape A.

### Đóng góp cụ thể

* Thay stub workflow, giữ nguyên chữ ký hàm và hướng dẫn của template; dùng get_claim_view, lookup_order, compute_compensation và finish.
* Truyền quote đầy đủ và crash_at vào issue_refund; host xử lý approval, trần theo đơn và idempotency. Không đưa ticket/secret/PII vào trace.
* Thêm 7 test, gồm 3 trường hợp crash/resume; tự chạy test và sinh báo cáo bằng công cụ của lab.

### Bằng chứng

* Commit kỹ thuật: 1e54dd0.
* Trên máy cá nhân: default pytest 61 passed, 248 deselected; student workflow 62 passed, 247 deselected.
* `src/reports/benchmark_workflow.json`: pass = pass^5 = 1.000; variance = 0.000000; cost/success = 34.29 VND mô phỏng; steps = 5.07.
* `src/reports/crash.json`: host crash_safety = 20/20; workflow có kiểm tra riêng cả ba cửa sổ crash trong `test_workflow.py`.
* Báo cáo cá nhân: `report/team/2A202604103_HoangMinh.md`.


## 2A202604037_TranAnhDung

### Phần việc phụ trách

* Shape C — Orchestrator & Bảo mật (`src/lab8/shapes/orchestrator.py`).
* Đóng gói handoff qua `lab8.handoff.make_handoff` (`handoff.v1`) và chạy investigator chỉ đọc qua `lab8.runtime.run_readonly_investigators`.
* Bảo đảm quote do code (`compute_compensation`) tính, truyền quote đầy đủ và `crash_at` tới `durability.issue_refund` (không bắt `InjectedCrash`).
* Rà soát payload trace và viết test bảo mật handoff/trace cho cả 3 shape (`workflow`, `single`, `orchestrator`).

### Đóng góp cụ thể

* Triển khai hoàn chỉnh Shape C trong `src/lab8/shapes/orchestrator.py` (đủ các nhánh `failed`, `needs_info`, `escalated`, `denied`, `resolved`).
* Tách bạch ranh giới bảo mật: `get_claim_view` + `make_handoff` allowlist, không truyền `parent_secret`, `raw_headers` hay raw order PII vào handoff hoặc trace.
* Tạo bộ test `src/tests/test_orchestrator_handoff_trace.py` (23 test case parametrize) kiểm tra allowlist handoff, `Trace contract v1`, `approval_claim_mismatch`, crash/resume và quét secret/PII trên cả 3 shape.
* Viết phần mô tả Shape C, handoff sanitization và bảo mật trace trong `report/team/group_report.md` và `report/team/decision_adr.md`.

### Bằng chứng

* Báo cáo cá nhân: `report/team/2A202604037_TranAnhDung.md`.
* File triển khai & test: `src/lab8/shapes/orchestrator.py`, `src/tests/test_orchestrator_handoff_trace.py`.
* `python -m pytest -q -m student -o addopts=`: 248 passed (mỗi shape `workflow`, `single`, `orchestrator`, `swarm` đạt 62/62).
* `python -m pytest -q`: 84 passed, 248 deselected (tại thời điểm chạy trước khi gộp thêm test của bạn 4).
* `python -m lab8.crash_test --count 20 --out reports/crash.json`: crash_safety 20/20.
* Commit triển khai, test và báo cáo: `381881f`, `ad12a74`.

## 2A202604120_NguyenQuocQuangAnh

### Phần việc phụ trách

* Ledger và đánh giá: bổ sung kiểm thử host, kiểm tra tích hợp các shape, chạy benchmark/crash và tổng hợp kết quả public.

### Đóng góp cụ thể

* Thêm `src/tests/test_member4_host_edges.py` với 7 ca kiểm tra approval, giới hạn tiền đã hoàn và crash/resume T14.
* Sau khi nhận code các shape, chạy ma trận kiểm thử host/student và tạo benchmark bốn shape cùng crash report.
* Tổng hợp số liệu, ghi nhận giới hạn cách tính cost và đề xuất workflow trong ADR.

### Bằng chứng

* Commit kỹ thuật/bằng chứng: `403cca7`.
* Test bổ sung: `src/tests/test_member4_host_edges.py` — 7 ca pass.
* Kiểm thử tích hợp: host 91 passed; student 248 passed.
* Benchmark: workflow, single và orchestrator đều 70/70; swarm 69/70.
* Crash suite: 20/20 cho host/swarm. Chưa có kết quả hidden chính thức.
