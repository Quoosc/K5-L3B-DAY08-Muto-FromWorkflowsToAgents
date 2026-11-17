# Người 4 — đánh giá sau tích hợp

Ngày 17/11/2026 (GMT+7). Code nhận từ `ad12a74`; commit test và bằng chứng `403cca7`.
Số liệu bảng dưới được trích bằng chương trình từ `src/reports/benchmark.json`.
Mỗi shape: 14 claim × 5 seed (11,22,33,44,55), DB mới cho mỗi trial,
as_of 2026-11-15, cùng MockLLM, pricing và evaluator.

| Shape | Pass rate | Pass^5 | Seed min–max | Variance | Cost/success VND | Mean/p95 steps |
| --- | --- | --- | --- | --- | --- | --- |
| workflow | 1.000000 | 1.000000 | 1.000000–1.000000 | 0.000000000 | 34.285714 | 5.071429/6 |
| single | 1.000000 | 1.000000 | 1.000000–1.000000 | 0.000000000 | 30.087143 | 2.000000/2 |
| orchestrator | 1.000000 | 1.000000 | 1.000000–1.000000 | 0.000000000 | 57.190000 | 4.714286/5 |
| swarm | 0.985714 | 0.928571 | 0.928571–1.000000 | 0.000816327 | 49.566957 | 2.800000/3 |

- Host gate: 91 passed, 248 deselected.
- Student matrix: 248 passed, 91 deselected (62 test mỗi shape).
- Crash suite: 20/20, `src/reports/crash.json`; phạm vi host/swarm.
- Trial benchmark duy nhất fail: `R-swarm-C-002-s55`, status resolved thay vì denied.
- A/B/C đều pass toàn bộ public; test swarm xác nhận lỗi cố ý nên student vẫn xanh.
- Không có student_drop, nhãn hidden hoặc kết quả hidden chính thức.

## Giới hạn khi diễn giải

Workflow có 0 model calls. Single gọi MockLLM nhưng bỏ kết quả; hàm decide
chọn hành động bằng nhánh Python. Orchestrator cũng dùng code để dựng handoff
và tính tiền. Không diễn giải kết quả thành năng lực model thật.
Workflow cộng tool cost cho lời gọi issue_refund; ba shape khác không cộng
chi phí ghi này. Không sửa Budget của thành viên hoặc thước đo để làm đẹp số.
Chênh lệch cost hiện gồm khác biệt cách đếm và số tool/model calls, chưa chứng
minh tác động riêng của topology. Steps chỉ là số event trace, không phải latency.
Cost mô phỏng VND; latency unavailable.

Môi trường Python 3.14.10/pytest 9.2.0/PyYAML 6.0.3 trên Windows AMD64;
cần chạy lại bằng Python 3.11–3.13/pytest >=8.3.4,<9 theo requirements lab.

## Rà soát ranh giới an toàn

Ba shape quote bằng compute_compensation, truyền quote đầy đủ vào host,
không tự trừ prior refund, xử lý quote=0 trước khi gọi host, dùng finish lấy
ledger/audit thực tế. Cả ba chuyển tiếp crash_at và cho InjectedCrash truyền ra.
Single/orchestrator bắt crash chỉ để flush trace rồi raise lại; điều này đáp ứng
T12, tương tự swarm tham chiếu. Handoff orchestrator chỉ có read tools.
Test bảo mật có 23 ca; kiểm 6 nhánh đại diện của cả ba shape, không chứng minh
mọi dữ liệu có thể có đều an toàn. Không có safety counts hidden để khai báo.

## Phần chưa thể chốt

Lần chạy `python -m lab8.check_submission` sau khi cập nhật báo cáo: 1 FAIL
(research card còn trống), 1 WARN (báo cáo chưa commit tại thời điểm chạy).
Ba shape đạt 12/12 public ở seed 11; benchmark và crash report được checker chấp nhận.

- Nhóm xác nhận đề xuất workflow trong ADR; public chưa đủ xác nhận gate hidden.
- Research card R1–R4 và một ablation: công việc chung, chưa có lựa chọn/nguồn từ nhóm.
- Người 2 chưa có test mới đã thêm/sửa trong commit bàn giao; chạy test có sẵn
  không đáp ứng nguyên văn yêu cầu đóng góp test của từng người.
- Hash chốt, LMS và quyền truy cập người chấm phải được xác nhận khi nộp.

## Lệnh tái lập

Chạy trong src/:

```text
python -m pytest -q
python -m pytest -q -m student -o addopts=
python -m lab8.benchmark --shapes workflow,single,orchestrator,swarm --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/benchmark.json
python -m lab8.crash_test --count 20 --out reports/crash.json
python -m lab8.check_submission
```
