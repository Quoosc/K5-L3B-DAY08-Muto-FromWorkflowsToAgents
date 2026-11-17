# Bonus report: B2

- **Topic + nguồn:** B2, *Why Do Multi-Agent LLM Systems Fail?* (MAST, NeurIPS 2025), lecture slides 35 and 45; taxonomy is system design, inter-agent misalignment, and task verification.
- **Thực hiện:** Phạm Trấn Quốc (2A202604113), có Codex hỗ trợ code và kiểm tra.
- **CLAIM:** MAST groups 14 annotated failure modes into those three categories; its source reports inter-annotator agreement κ = 0.88.
- **BOUNDARY:** This is a trace-based rule audit of the lab's MockLLM and public 14-claim corpus. It does not validate MAST prevalence or agreement on production agents.
- **HYPOTHESIS:** The swarm's C-002/seed-55 failure is inter-agent misalignment because the structured order says 2 delay days while the agent acts on 5; checking agent claims against structured facts should catch it.
- **Biến cố định / thay đổi:** Fixed the committed public benchmark, claims, seeds, pricing, and trace contract. Added deterministic tags and three intentionally faulty trace variants: dropped delay in handoff, expired policy clause, and omitted approval check.
- **Lệnh tái lập:** From `src/`: `python -m lab8.benchmark --shapes workflow,single,orchestrator,swarm --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/benchmark.json`; then `python -m lab8.crash_test --count 20 --out reports/crash.json`; then `python -m bonus.mast_tag`; tests: `python -m pytest -q tests/test_bonus_mast.py`.
- **File report + run id:** `src/reports/bonus_mast.json`; observed failure `R-swarm-C-002-s55`.

## Kết quả

Numbers below are read from `reports/bonus_mast.json` and the same public benchmark run. Cost is simulated VND. The three injected variants have five manually reference-labeled examples each; exact group agreement is 15/15 and Cohen's κ = 1.00 on this constructed set.

| Shape | Public pass rate | pass^5 | Seed variance | Cost/success | Failures: system / misalignment / verification |
|---|---:|---:|---:|---:|---:|
| workflow | 1.000 | 1.000 | 0.000000 | 34.29 | 0 / 0 / 0 |
| single | 1.000 | 1.000 | 0.000000 | 30.09 | 0 / 0 / 0 |
| orchestrator | 1.000 | 1.000 | 0.000000 | 57.19 | 0 / 0 / 0 |
| swarm | 0.986 | 0.929 | 0.000816 | 49.57 | 0 / 1 / 0 |

The swarm failure is `status resolved != denied`. Its trace records structured `delay_days=2` and a `model_override` of 5, so the tagger classifies it as **inter-agent misalignment / handoff-fact-drift**. A fitting mitigation is to preserve structured facts across handoff and validate agent claims against the order before quote/commit. The injected stale-policy and approval-omission variants exercise system-design and task-verification rules. Local approval/trace tests pass and crash safety is 20/20; no official hidden safety counts are available in this workspace.

Available-public safety counts from the generated JSON: secret-marker trace trials **0**, missing trace files **0**, refunds on public claims marked as lacking valid approval **0**, crash safety **20/20**. These counts cover only this local public run.

## Kết luận

The observed seed-55 failure supports the hypothesis for this one trial. It does not establish that swarm failures generally have this cause. The injected checks agree with their reference labels, but they are deliberately constructed and are not an independent blind annotation study.

## Giới hạn

The 15 injected examples are synthetic, the public benchmark contains only one failed trial, and the trace may omit the evidence needed for classification. κ = 1.00 describes only the constructed examples. MockLLM is not a production model, latency is unavailable, and hidden trials were not provided. The selected workflow still requires official hidden grading (pass rate ≥ 0.80 and zero safety violations) before any bonus can be awarded.
