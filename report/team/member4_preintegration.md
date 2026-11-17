# Người 4 — kiểm thử host trước khi nhận ba shape

> Ghi chú lịch sử trước tích hợp. Trạng thái mới nhất, số test và kết quả
> benchmark xem `member4_evaluation.md`. Ba shape hiện đã được nhận và kiểm tra;
> test/bằng chứng người 4 đã commit tại `403cca7`.

## Phạm vi và trạng thái

Ngày thực hiện: 17/11/2026 (GMT+7). HEAD nền: `034c6c4`.
Các thay đổi mô tả dưới đây chưa được commit; hash trên không phải commit chứa test mới.

Ba file `workflow.py`, `single.py`, `orchestrator.py` hiện vẫn gọi
`not_implemented`. Chưa có kết quả đánh giá implementation của người 1–3.
Tài liệu này là ghi chú kỹ thuật của phần kiểm thử, không thay thế báo cáo nhóm,
ADR, research card hoặc báo cáo cá nhân có MSSV/họ tên.

## Căn cứ từ source

| Yêu cầu | Source thực hiện | Test có sẵn |
| --- | --- | --- |
| Approval hợp lệ, đúng approval_id và đúng claim | `src/lab8/policy.py`, `src/lab8/durability.py` | `test_authorization.py`, `test_order_cap_and_approval_binding.py` |
| Một refund và một audit committed khi retry | `src/lab8/durability.py` | `test_refund_idempotency.py` |
| Trần theo đơn, T13 từ chối, T14 hoàn phần chênh | `src/lab8/policy.py` | `test_order_cap_and_approval_binding.py` |
| Tiền tính bằng code, policy hiện hành, không cộng ship và damage | `src/lab8/compensation.py` | `test_compensation.py` |
| Handoff allowlist, worker chỉ đọc | `src/lab8/handoff.py`, `src/lab8/runtime.py` | `test_handoff_secret.py` |
| Trace mới, đúng run_id và có events; quét sidecar | `src/lab8/metrics.py` | `test_trace_contract.py` |
| Retry/crash của từng shape sinh viên | `src/tests/test_public_matrix.py` | T11, T12, marker `student`; cần implementation của ba shape |

Đường dẫn test trong bảng nằm trong `src/tests/`. Không thay đổi các module
thước đo, config, data hoặc ba shape để thực hiện phần việc này.

## Test mới

File: `src/tests/test_member4_host_edges.py` (7 ca sau parametrization).
Các thay đổi dữ liệu chỉ nằm trong SQLite tạm do fixture `public_db` tạo;
không sửa fixture JSON public trong repo.

| Test | Khoảng trống được bổ sung | Kỳ vọng |
| --- | --- | --- |
| `test_non_positive_approval_denies_retries_without_effect` × 2 | Approval amount 0 và -1; từ chối lặp lại | Không effect, không committed audit; một audit denial cho cùng lý do |
| `test_dangling_approval_reference_does_not_pay` | Claim có approval_id nhưng bản ghi approval không tồn tại | `missing_approval`, không effect, có denial |
| `test_paid_cap_applies_to_remaining_amount_after_prior_refund` | Kết hợp paid cap với refund lịch sử | Paid 100.000, lịch sử 30.000, proposal/approval 150.000: effect mới 70.000, tổng 100.000 |
| `test_topup_crash_resumes_on_new_connection_once` × 3 | T14 crash ở cả ba điểm, đóng/mở connection rồi retry hai lần | Effect mới 120.000, tổng theo đơn 150.000, một audit committed, checkpoint 120.000 |

Số tiền kỳ vọng được viết trực tiếp từ luật nghiệp vụ và host cap; test không
dùng `compute_compensation` để tự sinh đáp án.

## Kết quả đã chạy

Mọi lệnh bên dưới chạy từ `src/`. Đây là kết quả thực tế trong workspace,
không phải kết quả hidden và không phải benchmark của ba shape sinh viên.

| Lệnh | Kết quả |
| --- | --- |
| `python -m pytest -q tests/test_member4_host_edges.py` | 7 passed |
| `python -m lab8.smoke` | `lab8.smoke pass` |
| `python -m pytest -q` | 61 passed, 248 deselected |
| `python -m lab8.crash_test --count 20 --out reports/crash.json` | `crash_safety 20/20`; file do CLI tạo |
| `python -m lab8.check_submission` | 13 FAIL, 1 WARN |

Phân loại 13 FAIL: ba shape chưa triển khai (3), thiếu benchmark (1), ADR còn
trống/sai giá trị Shape chọn (7), bảng đóng góp chưa điền (1), research card
chưa điền (1). WARN: các thay đổi chưa commit. Crash report đã được checker chấp nhận.

Môi trường: Windows AMD64, Python 3.14.10, pytest 9.2.0, PyYAML 6.0.3.
Repo yêu cầu Python 3.11–3.13 và pytest >=8.3.4,<9. Chưa xác nhận lần chạy
trên bộ phiên bản yêu cầu; `py -0p` báo không tìm thấy Python đã đăng ký.
Cần chạy lại các lệnh trên trong môi trường đúng phiên bản trước khi nộp.

`pytest` mặc định loại marker `student`. Crash suite gồm 17 lượt crash host,
kiểm conflict, retry thiếu approval và một lượt crash swarm. Hai kết quả xanh
này chưa chứng minh T11/T12 của ba shape sinh viên.

## Quy trình nhận code và kiểm tra tiếp

1. Ghi commit chứa code được bàn giao. Xác nhận ba shape giữ đúng chữ ký `run_claim`.
2. Chạy host gate và ma trận student; chuyển lỗi kèm shape/claim/seed cho tác giả.
3. Rà quote đầy đủ, ánh xạ status và trace ở mọi nhánh. Quote dương bị host từ chối
   cần audit `policy_denied`; không tự từ chối trước khi gọi host.
4. Kiểm T11/T12 trên từng shape. `crash_at` phải tới host và `InjectedCrash` phải
   truyền ra ngoài (có thể ghi trace rồi raise lại).
5. Rà trace/handoff và stdout: không dump claim/order thô; investigator chỉ đọc.
6. Chạy benchmark bốn shape và crash suite; đọc JSON sinh ra để điền bảng kết quả.
7. Nếu được phát `student_drop/`, chạy self-check. Không có nhãn thì không có pass rate.
8. Cùng nhóm chọn shape, chạy một ablation cho research card; điền ADR và báo cáo.
9. Commit code/bằng chứng, ghi hash và run id vào ADR theo `SUBMISSION.md`, rồi commit tiếp.
10. Chạy `check_submission`; xử lý FAIL, push và từng thành viên nộp link LMS.

### Các lệnh khi nhận đủ code

```text
python -m pytest -q
python -m pytest -q -m student -o addopts=
python -m pytest -q -m student -o addopts= -k "t11 or t12"
python -m lab8.benchmark --shapes workflow,single,orchestrator,swarm --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/benchmark.json
python -m lab8.crash_test --count 20 --out reports/crash.json
python -m lab8.check_submission
```

Self-check chỉ chạy khi có thư mục được giảng viên phát:

```text
python -m lab8.benchmark --shapes workflow,single,orchestrator --cases student_drop/hidden_claims.jsonl --world student_drop/hidden_world_state.json --out reports/hidden_selfcheck.json
```

### Bảng kết quả chờ benchmark

| Shape | Pass rate | Pass^5 | Seed min–max | Variance | Cost/success VND mô phỏng | Mean/p95 steps |
| --- | --- | --- | --- | --- | --- | --- |
| workflow | Chưa đo | Chưa đo | Chưa đo | Chưa đo | Chưa đo | Chưa đo |
| single | Chưa đo | Chưa đo | Chưa đo | Chưa đo | Chưa đo | Chưa đo |
| orchestrator | Chưa đo | Chưa đo | Chưa đo | Chưa đo | Chưa đo | Chưa đo |
| swarm | Chưa đo | Chưa đo | Chưa đo | Chưa đo | Chưa đo | Chưa đo |

Đọc các field tương ứng trong `benchmark.json` → `by_shape`: `pass_rate`,
`pass_5`, `seed_min`, `seed_max`, `seed_variance`, `cost_per_success_vnd`,
`mean_steps`, `p95_steps`. Run id dẫn chứng nằm trong `trials`.
Giữ cùng corpus, seed, MockLLM, pricing và evaluator. Mỗi trial dùng DB mới.
Chi phí là mô phỏng; latency là `unavailable`.

## Thông tin còn cần từ nhóm

- Họ tên, MSSV, email, GitHub của người 4 để tạo báo cáo cá nhân đúng tên và ghi TEAM.md.
- Commit code của từng shape để tái lập và ghi nhận tác giả/test thực tế.
- Kết quả benchmark, quyết định chung của nhóm và lựa chọn R1–R4/ablation.
- Bộ `student_drop/` nếu giảng viên phát; hidden labels và grader chính thức không có trong repo.

Không điền tên, commit đóng góp, kết quả hidden hoặc quyết định kiến trúc khi
chưa có dữ kiện. Khi đã commit test mới, dùng hash commit đó trong bảng đóng góp.

## AI hỗ trợ

Codex hỗ trợ rà source, viết test mới, chạy lệnh và soạn ghi chú này.
Bằng chứng tự kiểm hiện có là 7 test mới pass, host gate 61 pass và crash suite 20/20.
Thành viên cần đọc, tự giải thích test và ghi cách mình kiểm tra trong báo cáo cá nhân.
