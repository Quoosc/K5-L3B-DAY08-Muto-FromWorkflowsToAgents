# Research card

File này nằm cố định ở `report/team/research_card.md`; `python -m lab8.check_submission` đọc cột "Nhóm điền" bằng máy.

Phần này nối tiếp phần mini research ở buổi lý thuyết (slide 62–63). Chọn **một** câu R1–R4, điền 6 dòng, rồi biến nó thành **một ablation** chạy được trong lab: giữ nguyên model (MockLLM), tool, seed, corpus và giá, chỉ thay đổi một biến.

| Câu | Nguồn (thư viện tham khảo, slide 68–69) | Câu hỏi gợi ý cho lab |
| --- | --- | --- |
| R1 · Scaling | Google Research 2026, *Towards a Science of Scaling Agent Systems* | Task claims chủ yếu tuần tự hay song song được? Dự đoán thêm investigator sẽ làm pass rate và cost/success thay đổi thế nào. |
| R2 · Failure taxonomy | MAST, NeurIPS 2025, *Why Do Multi-Agent LLM Systems Fail?* | Các trial fail của swarm (seed 55) thuộc nhóm nào: lỗi giao việc, lệch mục tiêu, hay lỗi kiểm chứng? |
| R3 · Architecture choices | AgentArch, AACL 2026 | Nếu đổi topology mà giữ nguyên mọi thứ khác, biến nào phải cố định để kết luận còn đúng? |
| R4 · Evaluation confounders | EMNLP 2026, *Rethinking Evaluation of MAS Efficiency* | Làm sao chứng minh chênh lệch giữa A/B/C/D là do topology, không phải do prompt, tool hay seed? |

## Phiếu của nhóm

Điền vào cột cuối. Không xóa hai cột đầu.

| Field | Hướng dẫn | Nhóm điền |
| --- | --- | --- |
| CÂU | R1 / R2 / R3 / R4 | **R1 · Scaling** |
| SOURCE | Paper/blog, năm, URL, loại bằng chứng (benchmark, production report, blog kinh nghiệm) | Kim et al., “Towards a Science of Scaling Agent Systems” (2025 preprint; Google Research summary, 2026): [paper](https://arxiv.org/abs/2512.08296), [Google Research](https://research.google/blog/towards-a-science-of-scaling-agent-systems-when-and-why-agent-systems-work/). Nghiên cứu thực nghiệm/benchmark có kiểm soát; bài blog tóm tắt kết quả paper. |
| CLAIM | Một kết luận gốc của nguồn. Không viết rộng hơn phạm vi paper | Trong các benchmark và cấu hình được nghiên cứu, phối hợp nhiều agent cải thiện kết quả ở task có thể chia song song, nhưng các kiến trúc multi-agent được thử nghiệm làm giảm kết quả 39–70% trên task PlanCraft thiên về suy luận tuần tự. Không khái quát con số này cho LogiX-VN. |
| BOUNDARY | Model / dataset / setup giới hạn kết luận đó | Paper báo cáo 180 cấu hình trên Finance-Agent, BrowseComp-Plus, PlanCraft và Workbench, với ba họ model và năm kiến trúc. Đây không phải LogiX-VN, không dùng MockLLM hay bộ 14 public claim của lab; kết quả phụ thuộc task, model và cách phối hợp. Trong source LogiX, đường quyết định claim → order → quote → host là tuần tự do phụ thuộc dữ liệu; policy/history là các lần đọc phụ sau khi có claim. Runner hiện gọi các tool tuần tự, không tạo LLM investigator riêng. Ablation chỉ đo số lần gọi read-only trong orchestrator hiện tại, không đo latency hay hiệu ứng chạy song song. |
| HYPOTHESIS | Nếu đổi shape A→B (hoặc bật/tắt một thành phần), metric X sẽ đổi theo hướng nào, khoảng bao nhiêu | Public corpus có 13/14 claim cần order lookup. Khi giảm handoff từ ba read-only investigation calls xuống chỉ còn call bắt buộc `lookup_order`, dự đoán pass rate giữ ở 1.000000 và cost/success giảm khoảng 18.57 VND mô phỏng: 2 calls × 10 VND × 13/14 trial. Điều này kiểm tra lợi ích của hai lần đọc phụ trong implementation hiện tại, không phải lợi ích chung của multi-agent. |
| METHOD | Biến giữ cố định: model, tools, seed, corpus, giá, evaluator. Biến duy nhất được thay đổi: … | Chạy `orchestrator` và biến thể `r1_order_only` trên cùng 14 claim × 5 seed, `MockLLM`, world, pricing, `as_of`, DB mới mỗi trial và evaluator mặc định. Giữ nguyên orchestrator, quote, host/write path; chỉ đổi số read-only tools trong handoff từ 3 (`lookup_order`, `lookup_policy`, `lookup_refund_history`) xuống 1 (`lookup_order`). Lệnh chạy từ `src/`: `python -m lab8.benchmark --shapes orchestrator,r1_order_only --extra-shape r1_order_only=lab8.ablation_r1:run_claim --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/research_card_r1_ablation.json`. |
| FAILURE / METRIC | Một lỗi dự kiến và cách đo nó: pass rate, pass^5, variance, cost/success, leak, bypass | Lỗi dự kiến: bỏ nhầm một lần đọc làm thay đổi status/quote/ledger. Đo pass rate, pass^5, seed variance, cost/success, `tool_calls`, và so từng trial cùng claim/seed qua evaluator (status, amount, ledger, audit, trace và forbidden substrings). File benchmark không xuất riêng tổng leak/bypass count; không suy ra số đếm riêng nếu chưa chạy báo cáo safety tương ứng. Không dùng latency vì tài liệu metrics quy định latency MockLLM là `unavailable`. |

## Kết quả ablation

Phạm vi R1 trong lab: các lần đọc order, policy và history có thể tách sau khi biết claim/principal; quote vẫn chờ order, còn host chờ quote. Với cách triển khai hiện tại, tăng từ một lên ba lời gọi điều tra chỉ thêm dữ liệu phụ được ghi trace; quote tự đọc policy và host tự kiểm lịch sử. Nhóm dự đoán chiều tăng 1→3 giữ nguyên pass rate và tăng cost/success khoảng 18.57 VND mô phỏng. Ablation dưới đây đo chiều ngược 3→1. Đây là kiểm tra chi phí của phần điều tra phụ trong runner hiện tại; chưa đủ bằng chứng về scaling số agent độc lập hoặc speedup khi chạy song song.

Hypothesis định lượng được suy ra từ source và corpus public, không phải giả thuyết đăng ký trước độc lập với dữ liệu. Dự đoán sơ bộ trước lần chạy đầu là giảm khoảng 20 VND; sau khi rà nhánh thiếu order_id, công thức 2 × 10 × 13/14 giải thích mức giảm trung bình 18.57 VND.

- Lệnh đã chạy (copy nguyên văn): `python -m lab8.benchmark --shapes orchestrator,r1_order_only --extra-shape r1_order_only=lab8.ablation_r1:run_claim --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/research_card_r1_ablation.json` (chạy từ `src/`).
- Run id / file report: `src/reports/research_card_r1_ablation.json`; ví dụ `R-orchestrator-C-001-s11` và `R-r1_order_only-C-001-s11`.
- Kết quả so với hypothesis: hypothesis được ủng hộ trên public corpus. Cả hai cấu hình pass `70/70`, pass^5 `1.000000`, seed variance `0`; cost/success giảm từ `57.190000` xuống `38.618571` VND mô phỏng (giảm `18.571429`, xấp xỉ `32.5%`). Mean tool calls giảm từ `5.571429` xuống `3.714286`; tổng simulated cost giảm từ `4003.3` xuống `2703.3` VND. Không thấy lỗi theo evaluator ở cấu hình rút gọn.
- Giới hạn: MockLLM không phải model sản xuất, latency là `unavailable`. Biến thể giảm số lần đọc phụ, không thêm agent hay chạy investigator song song; kết quả chỉ áp dụng cho implementation và corpus public hiện tại, không chứng minh thêm agent nói chung không có ích.

Môi trường chạy: Windows, Python 3.14.10 / pytest 9.2.0 như lần đánh giá tích hợp; ngoài dải Python 3.11–3.13 và pytest <9 của lab. Cần tái lập trong môi trường đúng quy định trước khi nộp. Harness dùng patch tạm thời trong một tiến trình tuần tự; không dùng để chạy các trial đồng thời trong cùng tiến trình.

Kiểm thử bổ sung: `python -m pytest -q tests/test_research_r1.py` → 3 passed. Test kiểm kết quả tiền theo luật cho C-001, nhánh thiếu order C-004, định danh trace/shape, khôi phục patch khi crash và retry không tạo refund thứ hai. Codex hỗ trợ đọc nguồn, tạo harness/test, chạy benchmark và soạn phiếu; nhóm cần tự đọc và giải thích kết quả khi bảo vệ.
