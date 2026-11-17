# Decision record

Điền sau dấu `:` trên cùng dòng, không xóa nhãn. Giảng viên và `python -m lab8.check_submission` (chạy trong `src/`) đọc các dòng này bằng máy. Không đổi tên hay dời file này khỏi `report/team/`.
`Shape chọn` phải là đúng một trong: `workflow`, `single`, `orchestrator`, `swarm`. Đây là shape được chấm cổng hidden.

- Shape chọn:
- Commit hash:
- Run id dẫn chứng:
- Pass rate / pass^5 / seed min-max / variance:
- Cost per success (mô phỏng, VND):
- Crash safety:
- Secret leak / approval bypass:

Ví dụ một dòng đã điền: `- Shape chọn: workflow`, `- Crash safety: 20/20 (src/reports/crash.json)`.

## Vì sao shape này

Viết 1 đoạn. So cùng corpus và cùng seed, không so với một lần chạy lẻ.

## Có đáng đổi lấy multi-agent không

Nếu pass nhỉnh hơn mà cost và variance cao hơn, nhóm giữ hay đổi? Điều kiện nào làm quyết định đảo lại?

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
