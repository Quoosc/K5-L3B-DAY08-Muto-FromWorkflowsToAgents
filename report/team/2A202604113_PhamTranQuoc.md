# Báo cáo cá nhân — Phạm Trấn Quốc

## 1. Thông tin thành viên

- Họ tên: Phạm Trấn Quốc
- MSSV: 2A202604113
- Email: phamquoc896@gmail.com
- GitHub: [Quoosc](https://github.com/Quoosc)

## 2. Phần việc phụ trách

- Shape B — Single Agent của Lab 8.
- Triển khai vòng ReAct tối đa 8 bước trong `src/lab8/shapes/single.py`.
- Bảo đảm model chỉ được chọn read-only tools; model không được gọi `issue_refund`.
- Để code/host tính và kiểm soát số tiền hoàn, approval, idempotency và trần hoàn theo đơn.
- Xử lý crash/resume bằng cách truyền `crash_at` tới `durability.issue_refund` và không nuốt `InjectedCrash`.
- Ghi trace đúng contract, không ghi secret hoặc dữ liệu PII.

## 3. Đóng góp cụ thể

- Thay stub Single Agent bằng implementation hoàn chỉnh.
- Kết nối `connect`, `run_react`, `Budget`, `Trace`, `finish` và `issue_refund`.
- Xây dựng chuỗi read-only:
  `get_claim_view` → `lookup_order` → `compute_compensation`.
- Xử lý các trạng thái `failed`, `needs_info`, `escalated`, `denied` và `resolved`.
- Truyền quote đầy đủ cho host để host tự áp dụng approval và per-order cap; không tự trừ khoản đã hoàn.
- Thêm trace an toàn chỉ gồm trạng thái, định danh claim/order cần thiết và quote đã được lọc.

## 4. Bằng chứng

- File triển khai: `src/lab8/shapes/single.py`.
- Test Single Agent: `62 passed`.
- Host suite: `54 passed, 248 deselected`.
- Crash safety suite: `20/20`.
- Public benchmark Single Agent: pass rate `1.000`, pass^5 `1.000`, variance `0.000000`.
- Kiểm tra cú pháp bằng `py_compile`: đạt.
- Kiểm tra whitespace bằng `git diff --check`: đạt.

Các lệnh xác minh:

```powershell
cd src
python -m lab8.smoke
python -m pytest -q -m student -o addopts= -k single
python -m pytest -q
python -m lab8.crash_test --count 20 --out reports\single-crash.json
python -m lab8.benchmark --shapes single --cases data\public_claims.jsonl --seeds 11,22,33,44,55 --out reports\single-benchmark.json
```

Commit hash: cập nhật sau khi nhóm chốt commit.

## 5. Công cụ AI đã dùng

- Copilot SDK trong VS Code: đọc contract, đối chiếu reference shape và hỗ trợ viết implementation.
- PowerShell: tạo virtual environment, cài dependencies và chạy smoke/test/benchmark.
- Tự kiểm tra bằng test student, host suite, crash suite, benchmark và diff trước khi ghi nhận kết quả.

## 6. Tự đánh giá

Đã hoàn thành đầy đủ phần Single Agent được phân công và xác minh bằng toàn bộ test riêng của shape. Implementation giữ đúng ranh giới: model chỉ đọc và đề xuất, còn code/host quyết định quote và thực hiện refund an toàn.
