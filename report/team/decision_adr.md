# Decision record

Điền sau dấu `:` trên cùng dòng, không xóa nhãn. Giảng viên và `python -m lab8.check_submission` (chạy trong `src/`) đọc các dòng này bằng máy. Không đổi tên hay dời file này khỏi `report/team/`.
`Shape chọn` phải là đúng một trong: `workflow`, `single`, `orchestrator`, `swarm`. Đây là shape được chấm cổng hidden.

- Shape chọn: workflow
- Commit hash: 403cca7 (code và bằng chứng đánh giá public)
- Run id dẫn chứng: R-workflow-C-001-s11; R-swarm-C-002-s55; src/reports/benchmark.json
- Pass rate / pass^5 / seed min-max / variance: public 1.0 / 1.0 / 1.0–1.0 / 0.0; hidden chưa được chấm
- Cost per success (mô phỏng, VND): 34.285714285714285
- Crash safety: 20/20 (src/reports/crash.json, host/swarm); T12 student và 3 cửa sổ crash workflow đều pass
- Secret leak / approval bypass: không phát hiện qua các test public đã chạy; chưa có counts hidden chính thức, không suy thành hidden = 0

Ví dụ một dòng đã điền: `- Shape chọn: workflow`, `- Crash safety: 20/20 (src/reports/crash.json)`.

## Vì sao shape này

Đề xuất kỹ thuật của người 4 là workflow: đạt 70/70 public trial, pass^5 = 1.0,
không gọi model và có luồng cố định phù hợp bài toán hiện tại. Single và
orchestrator cũng đạt 70/70; swarm đạt 69/70, fail C-002 seed 55 vì tin ticket.
Đây là lựa chọn dựa trên public, cần cả nhóm xác nhận trước khi nộp và cần hidden
để biết có đạt ngưỡng 0.75 hay không. Không tuyên bố workflow rẻ nhất:
single có cost/success 30.09 so với workflow 34.29 trong lần đo hiện tại.

## Có đáng đổi lấy multi-agent không

Public chưa cho thấy tăng pass khi dùng orchestrator; cost/success là 57.19.
Chọn mức tự chủ thấp nhất đáp ứng công việc theo mục tiêu lab. Quyết định cần
xem lại nếu hidden cho thấy workflow thiếu khả năng xử lý cần thiết, hoặc task
mới cho phép phân rã song song/triển khai qua ranh giới agent có lợi được đo rõ.
Không suy rộng thành kết luận về mọi hệ thống multi-agent.

## Trace và bằng chứng

- **Các event được ghi trong trace:**
  - `workflow`: `claim` (`found`, `has_order`), `order` (`visible`, `reason`), `quote`, `refund_requested`, `refund_outcome`, `result`.
  - `single`: `react` (`stopped`, `status`), `claim_view` (`found`, `claim_id`, `order_id`) hoặc `order_lookup` (`visible`, `reason`, `order_id`) hoặc `quote`, và `crash` (khi gặp `InjectedCrash`).
  - `orchestrator`: `plan` (`claim_id`, `has_order_id`), `handoff` (đã sanitize qua `handoff.v1`), `investigator` (`lookup_order` theo `ORDER_FIELDS`, `policy_count`, `refund_history`), `quote`, `decision` / `host_outcome` / `error` / `crash`.
- **Các field cố ý KHÔNG ghi và lý do:**
  - Không ghi `parent_secret` (`CANARY_SECRET_*`) và `raw_headers_json` (chứa token `Bearer`) từ bảng `claims` vì đây là bí mật ở tầng parent, không được vượt qua ranh giới handoff hay lọt vào log.
  - Không ghi `phone`, `address`, `internal_note`, `item_name` từ bảng `orders` để tránh rò rỉ PII và ghi chú nội bộ.
  - Không ghi nguyên văn `ticket` thô vào trace để tránh rò nội dung người dùng / payload injection vào log kiểm toán.
- **Chứng minh hệ thống không lộ secret khi trace nằm ngoài phạm vi scanner:**
  - Trong `Trace contract v1`, grader chạy **fail-closed**: mọi file trace thiếu (`missing_trace`), cũ (`stale_trace`), sai định dạng (`invalid_trace`), sai `run_id` (`trace_run_id_mismatch`) đều bị tính **FAIL** vì scanner không thể chứng minh log sạch.
  - Để chứng minh không lộ secret: (1) mọi file phụ đều phải đặt cùng thư mục với `trace_path` và bắt đầu bằng `<run_id>` để `metrics.trace_files()` và `artifact_blob()` gom quét đầy đủ; (2) dùng allowlist trong code (`get_claim_view`, `ORDER_FIELDS`, `handoff.make_handoff`) chặn ngay từ nguồn tạo dữ liệu; (3) kiểm chứng bằng test tự động trong `src/tests/test_orchestrator_handoff_trace.py` quét cả `artifact_blob` lẫn `stdout`/`stderr` trên toàn bộ các nhánh của cả 3 shape (`84 passed`).

## Giới hạn

MockLLM không phải model sản xuất. Latency để `unavailable`. Không sửa JSON cho đủ 0.75.

Chi phí hiện bị ảnh hưởng cách ghi Budget: workflow tính thêm tool cost cho
`issue_refund`, còn single/orchestrator/swarm không tính lời gọi ghi này.
Single gọi MockLLM nhưng bỏ kết quả; nhánh Python trong `decide` chọn hành động.
Các lần gọi model và tool khác nhau giữa các shape, vì vậy so sánh này chưa
cô lập topology. Steps là số event trace, không phải số thao tác thực tế.
Môi trường chạy người 4 là Python 3.14.10/pytest 9.2.0, ngoài phiên bản lab quy định;
cần tái lập trên Python 3.11–3.13 và pytest >=8.3.4,<9.
