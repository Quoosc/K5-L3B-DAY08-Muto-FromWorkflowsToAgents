import json
from pathlib import Path

from bonus.mast_tag import analyze_manual_cases, build_report, tag_events

ROOT = Path(__file__).resolve().parents[1]


def test_three_intentional_fault_variants_are_tagged_and_agree_with_manual_labels():
    cases = json.loads((ROOT / "bonus" / "mast_cases.json").read_text(encoding="utf-8"))
    result = analyze_manual_cases(cases)
    assert len(cases) == 15
    assert {case["variant"] for case in cases} == {
        "handoff_drops_delay", "stale_policy_clause", "approval_check_omitted"
    }
    assert result["exact_agreement"] == 1.0
    assert result["cohen_kappa_group"] == 1.0


def test_swarm_seed_55_trace_is_tagged_as_inter_agent_fact_drift():
    trace = json.loads((ROOT / "traces" / "R-swarm-C-002-s55.json").read_text(encoding="utf-8"))
    tag = tag_events(trace["events"])
    assert tag["group"] == "inter_agent_misalignment"
    assert tag["mode"] == "handoff-fact-drift"


def test_report_counts_failures_and_retains_manual_audit():
    cases = json.loads((ROOT / "bonus" / "mast_cases.json").read_text(encoding="utf-8"))
    benchmark = json.loads((ROOT / "reports" / "benchmark.json").read_text(encoding="utf-8"))
    report = build_report(benchmark, ROOT / "traces", cases)
    assert report["manual_audit"]["n"] == 15
    assert report["failure_counts_by_shape"]["swarm"]["inter_agent_misalignment"] == 1
