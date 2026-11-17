# Báo cáo cá nhân — Nguyễn Quốc Quang Anh

## 1. Thông tin thành viên

- Họ tên: Nguyễn Quốc Quang Anh
- MSSV: 2A202604120
- Email: nguyenquocquanganh28@gmail.com
- GitHub: https://github.com/QuangAnh28
- Nhóm Muto, lớp L3B; vai trò: ledger + evaluation.

## 2. Phần việc phụ trách

Rà host policy/durability, bổ sung test độc lập với shape, kiểm tra tích hợp
ba shape đã bàn giao, sinh benchmark bốn shape và crash report, tổng hợp
kết quả public và giới hạn để nhóm lựa chọn kiến trúc.

## 3. Đóng góp cụ thể

- Commit kỹ thuật/bằng chứng: `403cca7`; bonus B2: `CODE_COMMIT_TBD`.
- Thêm `src/tests/test_member4_host_edges.py`, 7 ca: approval 0/âm, approval_id
  không tồn tại, paid cap sau prior refund và crash/resume T14 trên kết nối mới
  tại cả ba điểm injection. Đáp án tiền viết trực tiếp theo luật.
- Giữ nguyên module thước đo, config, data và code ba thành viên.
- Chạy host/student đầy đủ sau tích hợp; dùng CLI sinh `benchmark.json`, `crash.json`.
- Tổng hợp số đo, đề xuất workflow trong ADR và chỉ rõ cost accounting chưa đồng nhất.

## 4. Bằng chứng và tái lập

Chạy trong `src/`, trên Windows AMD64 / Python 3.14.10 / pytest 9.2.0 / PyYAML 6.0.3.
Phiên bản này ngoài Python 3.11–3.13 và pytest <9 mà lab yêu cầu; cần chạy lại
trong môi trường quy định trước khi nộp. Chưa có môi trường đó tại workspace.

| Lệnh | Kết quả thực tế sau tích hợp |
| --- | --- |
| `python -m pytest -q` | 91 passed, 248 deselected |
| `python -m pytest -q -m student -o addopts=` | 248 passed, 91 deselected |
| `python -m lab8.benchmark --shapes workflow,single,orchestrator,swarm --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/benchmark.json` | 280 trial; A/B/C mỗi shape 70/70; swarm 69/70 |
| `python -m lab8.crash_test --count 20 --out reports/crash.json` | 20/20 |

Số đo chi tiết ở `report/team/member4_evaluation.md`. Run id đối chứng:
`R-workflow-C-001-s11`, `R-swarm-C-002-s55`. Crash suite kiểm host/swarm;
crash shape sinh viên được kiểm qua T12 và test bổ sung. Không có student_drop
hoặc nhãn hidden; chưa xác nhận hidden pass rate hay safety counts chính thức.

## 5. Công cụ AI đã dùng

Codex hỗ trợ đọc source, viết test, chạy lệnh và soạn báo cáo. Kiểm chứng đã
thực hiện trong workspace bằng pytest và CLI lab, đối chiếu JSON với source.
Thành viên cần tự chạy lại và giải thích được test, quote đầy đủ, idempotency,
giới hạn benchmark và field cố ý không ghi trước khi bảo vệ bài.

## 6. Tự đánh giá

Bằng chứng workspace cho thấy bộ public và host đều xanh, crash suite 20/20.
Research card đã được cập nhật theo lựa chọn R1 của nhóm, kèm ablation đọc phụ
và report 140 trial; ba test bổ sung trong `src/tests/test_research_r1.py` đã pass.
Các giới hạn còn lại: môi trường phiên bản, hidden chưa phát/chấm, chưa đo
scaling số agent độc lập. Đây là ghi nhận bằng chứng kỹ thuật; chưa có dữ kiện
về trải nghiệm tự thực hiện hoặc tự đánh giá cá nhân ngoài các lần chạy đã ghi.

## 7. Bonus B2 — audit lỗi theo MAST

- Thêm `src/bonus/mast_tag.py` để đọc benchmark và trace, phân loại lỗi bằng quy tắc có lý do.
- Thêm 15 trace case tham chiếu cho ba fault variant: handoff làm lệch `delay_days`, chọn clause hết hạn, và bỏ bước kiểm approval.
- Thêm 3 kiểm thử trong `src/tests/test_bonus_mast.py`; kiểm tra seed 55 của swarm được gắn `inter_agent_misalignment / handoff-fact-drift`.
- Sinh `src/reports/bonus_mast.json`; trên các case dựng có chủ đích, exact agreement và Cohen's κ theo nhóm là 1.00. Kết quả này không phải đánh giá độc lập/blind.
- Commit: `CODE_COMMIT_TBD`. Hidden grader và hidden safety counts chưa được cung cấp; bonus gate chưa thể xác nhận.
