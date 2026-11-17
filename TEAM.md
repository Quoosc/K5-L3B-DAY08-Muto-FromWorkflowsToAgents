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

`python -m lab8.check\\\_submission` đọc bảng này bằng máy: giữ nguyên tiêu đề `## Bảng đóng góp` và các cột. Mỗi người một dòng: commit có nội dung và ít nhất một test đã thêm hoặc sửa.

|Người|Vai|Commit|Test đã thêm hoặc sửa|
|-|-|-|-|
|Hoàng Minh|Workflow + tích hợp|'1e54dd0'|'.\\.venv\\Scripts\\python.exe -m pytest -q -m student -o addopts= -k workflow' -62 passed|
|Phạm Trấn Quốc|Single agent|`5d118a5`|`python -m pytest -q -m student -o addopts= -k single` — 62 passed|
|Trần Anh Dũng|Orchestrator + handoff|`381881f`|`src/tests/test\\\_orchestrator\\\_handoff\\\_trace.py` (17 cases, 84 passed)|
|Nguyễn Quốc Quang Anh|Ledger + evaluation|||

## Cá nhân

Mỗi thành viên đồng thời tạo một báo cáo riêng trong `report/` theo dạng:

```text
report/team/MSSV\\\_HoTen.md
```

Ví dụ: `report/team/20241234\\\_NguyenVanAn.md`.

Sao chép mục dưới đây cho từng thành viên.

## MSSV\_HoTen

### Phần việc phụ trách

* 

### Đóng góp cụ thể

* 

### Bằng chứng

* 

## 2A202604113\_PhamTranQuoc

### Phần việc phụ trách

* Shape B — Single Agent.
* Triển khai vòng ReAct tối đa 8 bước trong `src/lab8/shapes/single.py`.
* Giữ model ở ranh giới read-only; code/host chịu trách nhiệm quote, approval và refund.
* Bảo đảm idempotency, per-order cap, crash/resume và trace không lộ secret/PII.

### Đóng góp cụ thể

* Thay stub Single Agent bằng implementation hoàn chỉnh.
* Kết nối `run\\\_react`, `Budget`, `Trace`, `finish` và `durability.issue\\\_refund`.
* Xử lý chuỗi `get\\\_claim\\\_view` → `lookup\\\_order` → `compute\\\_compensation`.
* Truyền quote đầy đủ cho host và chuyển tiếp `crash\\\_at` mà không bắt `InjectedCrash`.
* Giữ giới hạn step và đếm model/tool calls trong `Budget`.
* Xử lý đầy đủ các trạng thái của `RunResult`.
* Không lấy số ngày trễ từ ticket để quyết định compensation.
* Không tự trừ refund history trước khi gọi host.
* Giữ trace ở mức payload allowlist, không ghi raw claim/order row.

### Bằng chứng

* Báo cáo cá nhân: `report/team/2A202604113\\\_PhamTranQuoc.md`.
* 62 test Single Agent pass.
* Host suite: 54 passed.
* Crash safety: 20/20.
* Public benchmark Single Agent: pass rate 1.000, pass^5 1.000.
* Host suite: 54 passed, 248 deselected.
* Syntax check bằng `py\\\_compile`: đạt.
* `git diff --check`: đạt.
* Commit triển khai và báo cáo: `5d118a5`.
* Các seed benchmark: 11, 22, 33, 44, 55.
* Phạm vi kết luận: chỉ Shape B.

### Quy trình thực hiện

* Đọc `README.md`, `CHECKPOINTS.md`, `docs/contracts.md` và `docs/business\\\_rules.md`.
* Đối chiếu `runtime.py`, `tools.py`, `durability.py`, `trace.py` và shape swarm reference.
* Tạo môi trường Python 3.12 trong `src/.venv`.
* Cài dependencies từ `src/requirements.txt`.
* Chạy smoke, student matrix, host suite, crash suite và benchmark public.
* Đối chiếu kết quả với contract trước khi ghi vào báo cáo cá nhân.



# 2A202604103\_HoangMinh

### Phần việc phụ trách

* Shape A (`src/lab8/shapes/workflow.py`): chuỗi bước Python cố định; tiền do code tính, host kiểm duyệt và ghi refund.
* Test cá nhân: `src/tests/test\\\_workflow.py`; benchmark riêng Shape A.

### Đóng góp cụ thể

* Thay stub workflow, giữ nguyên chữ ký hàm và hướng dẫn của template; dùng get\_claim\_view, lookup\_order, compute\_compensation và finish.
* Truyền quote đầy đủ và crash\_at vào issue\_refund; host xử lý approval, trần theo đơn và idempotency. Không đưa ticket/secret/PII vào trace.
* Thêm 7 test, gồm 3 trường hợp crash/resume; tự chạy test và sinh báo cáo bằng công cụ của lab.

### Bằng chứng

* Commit kỹ thuật: 1e54dd0.
* Trên máy cá nhân: default pytest 61 passed, 248 deselected; student workflow 62 passed, 247 deselected.
* `src/reports/benchmark\\\_workflow.json`: pass = pass^5 = 1.000; variance = 0.000000; cost/success = 34.29 VND mô phỏng; steps = 5.07.
* `src/reports/crash.json`: host crash\_safety = 20/20; workflow có kiểm tra riêng cả ba cửa sổ crash trong `test\\\_workflow.py`.
* Báo cáo cá nhân: `report/team/2A202604103\\\_HoangMinh.md`.



