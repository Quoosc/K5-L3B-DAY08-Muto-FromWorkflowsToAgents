# Báo cáo nhóm — Lab 8 LogiX-VN

## 1. Thông tin nhóm

- Nhóm: **Muto** — lớp **L3B**.
- Thành viên: Hoàng Minh, Phạm Trấn Quốc, Trần Anh Dũng, Nguyễn Quốc Quang Anh.
- Repo: [K5-L3B-DAY08-Muto-FromWorkflowsToAgents](https://github.com/Quoosc/K5-L3B-DAY08-Muto-FromWorkflowsToAgents).
- Commit code và bằng chứng đánh giá: `403cca7`, trùng tham chiếu trong [ADR](decision_adr.md). Đây chưa phải xác nhận commit nộp cuối của nhóm.
- Phạm vi kết quả: bộ public; chưa có kết quả hidden chính thức.

## 2. Mục tiêu và cách tiếp cận

Nhóm triển khai cùng quy trình xử lý claim LogiX-VN bằng workflow, single agent và orchestrator, sau đó so sánh với swarm tham chiếu có sẵn. Mục tiêu là chọn kiến trúc ít tự chủ nhất vẫn đáp ứng công việc, dựa trên độ đúng, độ ổn định và chi phí mô phỏng.

Nguồn sự thật là order có cấu trúc và policy hiện hành tại `as_of = 2026-11-15`. Ticket được coi là dữ liệu người dùng, không phải lệnh và không quyết định số tiền. Tiền được tính bằng code; approval, trần hoàn tiền và idempotency do host kiểm tra.

Nhóm chia việc theo ba shape và một vai kiểm thử/đánh giá. Người 4 bổ sung test host trước khi nhận code, sau đó chạy ma trận student trên các shape đã bàn giao, benchmark đủ bốn shape và crash suite của host/swarm. Chi tiết phân công và commit nằm trong [TEAM.md](../../TEAM.md).

## 3. Giải pháp

### 3.1. Workflow — Shape A

`workflow.py` chạy chuỗi bước Python cố định: `get_claim_view` → `lookup_order` theo principal → `compute_compensation` → `durability.issue_refund` nếu quote dương. Shape không dùng model và không lấy số ngày trễ trong ticket để tính tiền.

Claim không tồn tại trả `failed`; thiếu `order_id` trả `needs_info`; đơn không visible trả `escalated`; quote bằng 0 trả `denied`. Khi host trả conflict, shape trả `failed`; host từ chối thông thường trả `denied`. Trace ghi metadata, quote và outcome, được flush trong `finally`; kết nối SQLite cũng được đóng tại đây.

### 3.2. Single agent — Shape B

`single.py` sử dụng `run_react` với `worker=True`, tối đa 8 bước. Các tool được chọn trong flow là `get_claim_view`, `lookup_order` và `compute_compensation`. Sau vòng lặp, code chuyển quote dương cho host; model không có quyền ghi refund.

Implementation gọi MockLLM ở mỗi lần `decide`, có ghi usage vào `Budget`. Tuy nhiên, đầu ra MockLLM không được dùng để chọn hành động: tool tiếp theo được chọn bằng các nhánh Python dựa trên `last_tool` và kết quả đọc. Đây là giới hạn cần nêu khi diễn giải kiến trúc single hiện tại. Trace ghi trạng thái vòng lặp, một payload kết quả đọc đã chọn lọc và event crash khi có.

### 3.3. Orchestrator — Shape C

`orchestrator.py` đọc claim, gọi MockLLM ở bước plan, rồi dựng handoff bằng `make_handoff`. Investigator nhận ba tool đọc: `lookup_order`, `lookup_policy`, `lookup_refund_history`. Orchestrator lấy order view từ investigator để tính quote bằng code và gọi host. Handoff không cấp tool ghi; kết quả plan của MockLLM không quyết định nội dung handoff trong implementation hiện tại.

Trace ghi `plan`, handoff đã sanitize, kết quả investigator đã lọc, `quote` và các event kết thúc phù hợp. Khi có `InjectedCrash`, single và orchestrator ghi trace rồi raise lại; exception không bị chuyển thành thành công.

### 3.4. Tiền, approval và crash

`compute_compensation` chỉ xét policy có `is_current` và ngày hiệu lực không vượt `as_of`. Đơn đã giao đủ điều kiện trễ từ ba ngày được hoàn phí ship; damage đã xác minh được giới hạn theo policy và số tiền đã trả. Nếu cả hai đủ điều kiện, quote lấy số lớn hơn, không cộng ship với damage.

Cả ba shape truyền **quote đầy đủ** vào `issue_refund`, không tự trừ refund history. Host kiểm approval mà claim trỏ tới, approval phải thuộc đúng claim và còn hiệu lực; sau đó áp dụng trần theo đơn, approval và paid amount. Ví dụ T14: proposal 150.000 VND, lịch sử hoàn 30.000 VND, effect mới 120.000 VND.

Host dùng khóa `refund:{claim_id}`; refund và audit `refund_committed` nằm trong cùng transaction. Retry không tạo effect thứ hai; amount conflict giữ dòng đã commit. Shape truyền `crash_at` xuống host và cho crash truyền ra ngoài. `finish()` đọc effect/audit thực tế từ SQLite để tạo `RunResult`.

### 3.5. Handoff và trace an toàn

Handoff dùng allowlist `ALLOWED_FIELDS` và `FACT_KEYS`, chỉ cấp tool đọc. Trace không ghi nguyên claim/order row, ticket, `parent_secret`, raw headers, số điện thoại, địa chỉ, internal note hoặc tên hàng. Workflow chỉ ghi metadata order; orchestrator có ghi order view theo allowlist `ORDER_FIELDS`.

Mọi lần trả kết quả đều ghi JSON mới có `run_id` khớp và `events` là list. Bộ test handoff/trace gồm 23 ca, trong đó kiểm sáu nhánh đại diện trên cả ba shape và quét cả artifact lẫn stdout/stderr. Đây là bằng chứng trên các ca được kiểm tra, không phải bảo đảm tuyệt đối cho mọi input.

## 4. Kết quả và đề xuất kiến trúc

Benchmark dùng cùng 14 public claim, seed `11,22,33,44,55`, MockLLM, bảng giá và evaluator; mỗi trial có SQLite mới. Tổng cộng 280 trial. Bảng dưới lấy từ [benchmark.json](../../src/reports/benchmark.json), các số thập phân được làm tròn để trình bày.

Pass rate tính theo trial; pass^5 là tỷ lệ claim pass cả năm seed. Variance là phương sai tổng thể của năm pass rate theo seed. Cost/success tính cả chi phí trial fail; steps đếm số event trace theo evaluator.

| Shape | Trial pass | Pass rate | Pass^5 | Seed min–max | Variance | Cost/success VND mô phỏng | Mean/p95 steps |
| --- | --- | --- | --- | --- | --- | --- | --- |
| workflow | 70/70 | 1.000000 | 1.000000 | 1.000000–1.000000 | 0.000000000 | 34.285714 | 5.071429/6 |
| single | 70/70 | 1.000000 | 1.000000 | 1.000000–1.000000 | 0.000000000 | 30.087143 | 2.000000/2 |
| orchestrator | 70/70 | 1.000000 | 1.000000 | 1.000000–1.000000 | 0.000000000 | 57.190000 | 4.714286/5 |
| swarm | 69/70 | 0.985714 | 0.928571 | 0.928571–1.000000 | 0.000816327 | 49.566957 | 2.800000/3 |

Swarm fail duy nhất ở `R-swarm-C-002-s55`: ticket khai trễ 5 ngày, order là 2 ngày nhưng swarm trả `resolved` thay vì `denied`. Đây là điểm yếu có chủ đích của shape tham chiếu. Test student vẫn xanh vì riêng trial đó được kiểm là phải fail nghiệp vụ.

Kết quả kiểm thử tích hợp trong workspace:

| Kiểm tra | Kết quả | Phạm vi |
| --- | --- | --- |
| Host gate | 91 passed, 248 deselected | Test mặc định, gồm test bổ sung của nhóm |
| Student matrix | 248 passed, 91 deselected | 62 test/shape; gồm retry T11 và crash/resume T12 |
| Crash suite | 20/20 | Host và một kịch bản swarm, xem [crash.json](../../src/reports/crash.json) |
| Tái lập hai report | Khớp toàn bộ object JSON | Chạy lại benchmark và crash suite trên DB tạm |
| Check submission tại `5bc8076` | 1 FAIL, 0 WARN | Research card còn trống |

Người 4 đề xuất **workflow** theo mục tiêu ít tự chủ nhất: đạt 70/70 public trial và không gọi model. Single cũng đạt toàn bộ public và có cost/success thấp hơn trong cách đếm hiện tại, nên không kết luận workflow rẻ nhất. Orchestrator chưa tăng độ đúng trên corpus này. Đề xuất và điều kiện đổi quyết định được ghi trong [ADR](decision_adr.md), cần nhóm xác nhận trước khi nộp.

Chưa có `student_drop/` hoặc kết quả grader hidden. Vì vậy chưa xác nhận ngưỡng hidden 0,75, secret leak count hoặc approval bypass count chính thức. [Research card](research_card.md) và ablation chưa hoàn thành.

## 5. Khó khăn và cách xử lý

Môi trường người 4 dùng Windows AMD64, Python 3.14.10, pytest 9.2.0 và PyYAML 6.0.3. Hai lệnh `python -m pytest -q` và `python -m pytest -q -m student -o addopts=` cho kết quả lần lượt 91 và 248 test pass. Tuy nhiên, lab quy định Python 3.11–3.13 và pytest >=8.3.4,<9; cần tái lập trong môi trường đúng phiên bản trước khi nộp. Các lần chạy hiện tại được ghi kèm giới hạn này.

Qua rà source, workflow cộng tool cost cho `issue_refund`, còn ba shape khác không cộng chi phí lời gọi ghi này. Nhóm giữ nguyên số liệu report, ghi nhận khác biệt cách đếm khi so sánh; chưa thực hiện thí nghiệm chuẩn hóa cách đếm để quy tác động riêng cho topology.

Các lệnh tái lập benchmark, crash và kiểm bài nộp nằm trong [báo cáo đánh giá người 4](member4_evaluation.md); mọi lệnh chạy từ `src/`.

## 6. Tổng hợp đóng góp

| Thành viên | Đóng góp và bằng chứng |
| --- | --- |
| Hoàng Minh | Workflow, test `test_workflow.py` gồm 7 ca; commit `ca4e254`, `1e54dd0`. |
| Phạm Trấn Quốc | Single với `run_react`, Budget, trace và host gate; commit `5d118a5`. Dòng đóng góp hiện ghi chạy 62 test có sẵn; chưa có test mới đã thêm/sửa trong commit bàn giao được rà. |
| Trần Anh Dũng | Orchestrator, handoff/trace; test `test_orchestrator_handoff_trace.py` gồm 23 ca sau tham số hóa; commit `381881f`, `ad12a74`. |
| Nguyễn Quốc Quang Anh | Thêm 7 ca host edge, kiểm thử tích hợp, benchmark/crash, tổng hợp metric và đề xuất ADR; commit kỹ thuật/bằng chứng `403cca7`, báo cáo `5bc8076`, rà soát `8c4205a`. |

Báo cáo cá nhân nằm trong `report/team/`, đặt tên theo MSSV và họ tên từng thành viên. Các số 54/61/84 test trong báo cáo cá nhân là kết quả được ghi ở các thời điểm trước tích hợp; kết quả kiểm tra chung hiện dùng 91 host test và 248 student test như mục 4.

## 7. Hạn chế và hướng cải thiện

MockLLM có kết quả cố định theo seed, không đại diện model sản xuất; chi phí là mô phỏng và latency là `unavailable`. Steps đếm event trace, không phải số thao tác thực tế; các shape ghi trace ở mức chi tiết khác nhau. Prompt, số model/tool calls và cách đếm host write chưa giống nhau, nên benchmark chưa cô lập tác động topology bằng ablation.

Bộ public ít claim và swarm có lỗi được thiết kế trước. Chưa có kết quả hidden, research card hoặc ablation để kiểm chứng giả thuyết nghiên cứu. Nhóm cần hoàn thành các phần này, xác nhận lựa chọn kiến trúc và tái lập bằng đúng phiên bản môi trường. Quyết định cần xem lại nếu hidden cho thấy workflow không đáp ứng yêu cầu, hoặc task mới tạo lợi ích agent/song song được đo rõ.

## 8. Tài liệu tham khảo

- Đề bài và cách chấm: [README.md](../../README.md), [RULES.md](../../RULES.md), [RUBRIC.md](../../RUBRIC.md), [SUBMISSION.md](../../SUBMISSION.md).
- Luật và contract: [business_rules.md](../../docs/business_rules.md), [contracts.md](../../docs/contracts.md), [metrics.md](../../docs/metrics.md).
- Implementation: `src/lab8/shapes/`, `src/lab8/policy.py`, `src/lab8/durability.py`, `src/lab8/handoff.py` và `src/lab8/runtime.py`.
- Bằng chứng: `src/reports/benchmark.json`, `src/reports/crash.json`, `src/tests/test_member4_host_edges.py`, `src/tests/test_workflow.py`, `src/tests/test_orchestrator_handoff_trace.py`.

Chưa bổ sung nguồn nghiên cứu bên ngoài cho research card.
