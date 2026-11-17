# Báo cáo cá nhân — Phạm Trấn Quốc
## 1. Thông tin thành viên
- Họ tên: Phạm Trấn Quốc
- MSSV: 2A202604113
- Email: phamquoc896@gmail.com
- GitHub: [Quoosc](https://github.com/Quoosc)
- Nhóm: Muto; lớp: L3B.
- Shape phụ trách: B — Single Agent.
## 2. Phạm vi được phân công
Phụ trách implementation Shape B trong Lab 8, tập trung tại
`src/lab8/shapes/single.py`.
Giữ nguyên chữ ký public `run_claim` và output contract `RunResult`.
Triển khai vòng ReAct bounded tối đa 8 bước, trong đó model chỉ chọn
read-only tools và không được gọi `issue_refund`.
Để code và host quyết định quote, approval, per-order cap, idempotency
và việc ghi refund.
Truyền `crash_at` xuống `durability.issue_refund`, không bắt hoặc che giấu
`InjectedCrash`, đồng thời tạo trace mới cho mỗi lần chạy.
Tự setup môi trường, chạy smoke, student tests, host suite, crash suite và
benchmark riêng để cung cấp bằng chứng cho nhóm.
## 3. Mục tiêu kỹ thuật
Shape B mô phỏng một agent đơn có khả năng đọc dữ liệu và chọn bước tiếp
theo, nhưng không được vượt qua ranh giới an toàn của host.
Nguồn sự thật là order row và policy hiện hành; ticket là dữ liệu người
dùng, không phải lệnh và không phải cơ sở tính tiền.
Agent không tin số ngày trễ do khách viết, không tự tính net refund và
không tự ghi trực tiếp vào `refund_ledger`.
Host mới kiểm tra approval, ownership, giới hạn theo order và idempotency.
Trace phải có `run_id` khớp kết quả trả về và không chứa secret, header,
phone, address, item name hoặc internal note.
## 4. Kiến trúc implementation
`run_claim` mở SQLite store bằng `lab8.db.connect`, gọi `_run` và đóng
connection trong `finally`.
`_run` tạo `Budget` để đếm model calls, tool calls, token và chi phí mô
phỏng; tạo `run_id` bằng `make_run_id("single", claim_id, seed)`.
Trace được khởi tạo ngay đầu flow để mọi nhánh, kể cả nhánh sớm và crash,
có thể ghi bằng chứng.
Decision function nhận observation từ `run_react`, sau đó chỉ trả về một
read-only tool hoặc final result.
Runtime được gọi với `worker=True` và `max_steps=8`, giúp giới hạn autonomy
và để runtime từ chối các write tools.
Khi có final result, code chuyển sang bước host; khi hết step cap, flow
trả `failed` thay vì chạy vô hạn.
## 5. Luồng ReAct
Lượt đầu chọn `get_claim_view` để lấy các field tối thiểu cần cho flow.
Claim không tồn tại được trả `failed`; claim thiếu `order_id` được trả
`needs_info`, không đoán order id từ ticket.
Claim hợp lệ tiếp tục chọn `lookup_order` với `order_id` và `principal_id`.
Tool này kiểm tra order tồn tại và thuộc đúng principal hay không.
Order không visible được trả `escalated`; shape không trả dữ liệu nhạy cảm
của order ở nhánh này.
Order visible được chuyển sang `compute_compensation`, sử dụng structured
order fields và policy hiện hành.
Quote bằng 0 được trả `denied`; quote dương được giữ nguyên để gửi host.
Model không có bước nào được phép gọi write tool hoặc quyết định effect
amount cuối cùng.
## 6. Ranh giới model, code và host
Model chỉ chọn công cụ đọc trong vòng ReAct và được tính vào `Budget`.
Model không ghi ledger, không tạo `refund_committed`, không bỏ qua approval,
không bỏ qua principal scope và không tự quyết định tiền.
Code lấy quote từ `compute_compensation` rồi truyền quote đầy đủ sang
`issue_refund`.
Host kiểm tra approval gắn với đúng claim; approval thiếu, hết hạn, invalid
hoặc sai claim đều bị từ chối.
Host áp dụng giới hạn approved amount, paid amount và cap theo order.
Host bảo đảm idempotency bằng `refund:{claim_id}` và là cổng duy nhất ghi
effect vào ledger.
Thiết kế này ngăn câu trả lời chữ của model trở thành bằng chứng refund
giả hoặc bypass policy.
## 7. Xử lý trạng thái và output
- `failed`: claim không tồn tại, step cap, trạng thái bất thường hoặc amount conflict.
- `needs_info`: claim không có order id.
- `escalated`: order không tồn tại hoặc ngoài principal scope.
- `denied`: quote không có entitlement hoặc host từ chối quote.
- `resolved`: host ghi refund thành công.
`proposal_amount` luôn là quote đầy đủ, không phải net effect sau cap.
`refund_effects` và `committed_audit_count` được `finish` đọc lại từ
database, không được shape tự điền bằng giá trị suy đoán.
Nếu host trả policy denial, shape trả `denied`; nếu host trả conflict,
shape trả `failed` và giữ nguyên effect cũ.
## 8. Idempotency và per-order cap
Shape không tự trừ refund history trước khi gọi host vì host đã áp dụng cap
theo order.
T13 kiểm tra entitlement đã được hoàn đủ; T14 kiểm tra entitlement mới
lớn hơn và chỉ được hoàn phần chênh lệch.
Cả hai case đều yêu cầu shape truyền quote đầy đủ để host tính effect.
Retry cùng claim không tạo thêm dòng ledger hoặc audit committed.
Retry với amount khác không sửa effect cũ và được ghi nhận là conflict.
## 9. Crash và resume
`crash_at` nhận từ chữ ký public và được truyền nguyên xuống
`issue_refund`; `InjectedCrash` không bị bắt để biến crash thành success.
Trước khi ném crash, trace được flush để giữ bằng chứng lần chạy.
Sau crash tại `after_effect_before_checkpoint`, effect có thể đã tồn tại
trong SQLite; lần resume dùng cùng store và host thực hiện idempotent replay.
Resume không tạo refund thứ hai. Test T12 và crash suite kiểm chứng hành vi
này trên nhiều scenario.
Kết quả crash safety của Shape B là `20/20`.
## 10. Trace và bảo mật
Trace dùng cùng `run_id` với `RunResult`, được ghi thành JSON trong
thư mục `traces` và có object gốc gồm `run_id`, `steps`, `events`.
Event React chỉ ghi stopped status và status cuối; claim view chỉ ghi
found, claim id và order id cần thiết.
Order event chỉ ghi visible, reason và order id; quote event chỉ ghi
compensation payload đã allowlist.
Không ghi nguyên claim row, order row, `parent_secret`, `raw_headers`,
phone, address, item name hoặc internal note.
Event crash chỉ ghi điểm injection. Cách ghi này phù hợp Trace contract v1
và cho phép leak scanner kiểm tra artifact.
## 11. Setup môi trường
Môi trường sử dụng Python 3.12.10 trên Windows AMD64.
Virtual environment được tạo tại `src/.venv`; dependencies được cài từ
`src/requirements.txt`.
Smoke test chạy trước ma trận student và trả về `lab8.smoke pass`.
Syntax được kiểm tra bằng `py_compile`; whitespace được kiểm tra bằng
`git diff --check`.
Không sửa `metrics.py`, `durability.py`, `policy.py`, config hoặc data.
Không sửa test để làm đẹp kết quả và không dùng JSON report thủ công.
## 12. Bằng chứng kiểm thử
Student command:
`python -m pytest -q -m student -o addopts= -k single`
Kết quả: `62 passed`.
Host command:
`python -m pytest -q`
Kết quả: `93 passed, 248 deselected`.
Crash command:
`python -m lab8.crash_test --count 20 --out reports\single-crash.json`
Kết quả: `crash_safety 20/20`.
Benchmark command:
`python -m lab8.benchmark --shapes single --cases data\public_claims.jsonl --seeds 11,22,33,44,55 --out reports\single-benchmark.json`
Kết quả riêng của Shape B: pass rate `1.000`, pass^5 `1.000`,
variance `0.000000`, seed min/max `1.000/1.000`.
Cost benchmark là cost mô phỏng, không phải hóa đơn API.
## 13. Case và quyết định kỹ thuật
Student matrix bao phủ entitlement shipping, claim không đủ điều kiện,
thiếu order id, sai principal, prior refund, damage entitlement, retry và
crash resume.
Chọn `run_react` thay vì tạo vòng lặp riêng để dùng chung step cap và
dispatch policy của runtime.
Chọn `worker=True` để runtime chặn write tools thay vì chỉ dựa vào prompt.
Chọn `compute_compensation` để code sở hữu logic tiền và không dùng ticket
parser cho quyết định quote.
Chọn `finish` và `Trace` có sẵn để thống nhất RunResult và trace contract.
Chọn quote đầy đủ khi gọi host để không trừ cap hai lần ở T13/T14.
## 14. Công cụ, hạn chế và tự kiểm tra
Copilot SDK trong VS Code được dùng để đọc cấu trúc repo, contract và
reference shape; PowerShell được dùng để setup và chạy lệnh.
AI output chỉ được giữ sau khi đã chạy test; mọi thay đổi được đối chiếu
với diff và contract.
MockLLM là stand-in deterministic, không phải model production; latency
được ghi là `unavailable` và cost là chi phí mô phỏng.
Nếu dùng model thật, cần test prompt injection rộng hơn. Nếu concurrency
tăng, cần benchmark lock contention của SQLite và race giữa các claim.
## 15. Bảng đối chiếu yêu cầu
| Yêu cầu | Cách đáp ứng | Bằng chứng |
|---|---|---|
| ReAct bounded | `max_steps=8` | `single.py` |
| Read-only agent | `worker=True` | `runtime.py` |
| Code quyết tiền | `compute_compensation` | `tools.py` |
| Host quyết định refund | `issue_refund` | `durability.py` |
| Approval binding | host policy | T01–T14 |
| Per-order cap | truyền quote đầy đủ | T13, T14 |
| Idempotency | replay theo claim | T11 |
| Crash safety | forward `crash_at` | T12, 20/20 |
| Trace mới | `Trace(run_id)` | trace contract |
| Không lộ secret | payload allowlist | trace checks |
| Output thống nhất | `finish` | `common.py` |
## 16. Commit và tự đánh giá
- Commit implementation: `5d118a5`.
- Commit test bổ sung: `f974e1e`.
- Nội dung test bổ sung: trace Single Agent an toàn và retry giữ một refund/một audit.
- File code: `src/lab8/shapes/single.py`.
- File báo cáo: `report/team/2A202604113_PhamTranQuoc.md`.
- Người thực hiện: Phạm Trấn Quốc / Quoosc.
- File test bổ sung: `src/tests/test_single_agent.py`.
- Kết quả test bổ sung: `2 passed`.
Shape B đã hoàn thành theo contract của lab: agent chỉ đọc và đề xuất,
host là nơi duy nhất ghi refund, quote dựa trên structured data, retry không
tạo effect thứ hai, crash resume an toàn và trace có payload sạch.
Kết quả đã được xác minh bằng lệnh chạy thực tế. Benchmark tổng, ADR và
research card vẫn là trách nhiệm chung của nhóm và không được suy ra chỉ từ
benchmark riêng của Shape B.

### Xác nhận phạm vi

Báo cáo này chỉ ghi nhận phần việc và bằng chứng do Phạm Trấn Quốc thực hiện.
