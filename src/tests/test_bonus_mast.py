import json
from pathlib import Path

from bonus.mast_tag import analyze_manual_cases, build_report, tag_events
from bonus.fault_trials import run_fault_trials

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
    events = [
        {"kind": "investigator", "payload": {"lookup_order": {
            "order": {"delay_days": 2}}}},
        {"kind": "model_override", "payload": {"delay_days": 5}},
    ]
    tag = tag_events(events)
    assert tag["group"] == "inter_agent_misalignment"
    assert tag["mode"] == "handoff-fact-drift"


def test_report_counts_failures_and_retains_manual_audit():
    cases = json.loads((ROOT / "bonus" / "mast_cases.json").read_text(encoding="utf-8"))
    benchmark = json.loads((ROOT / "reports" / "benchmark.json").read_text(encoding="utf-8"))
    report = build_report(benchmark, ROOT / "traces", cases)
    assert report["manual_audit"]["n"] == 15
    # The checked-in generated report records the result from the actual public trace;
    # tests remain runnable from a clean clone where traces/ is intentionally ignored.
    saved = json.loads((ROOT / "reports" / "bonus_mast.json").read_text(encoding="utf-8"))
    failure = saved["benchmark_failures"][0]
    assert (failure["run_id"], failure["group"], failure["mode"]) == (
        "R-swarm-C-002-s55", "inter_agent_misalignment", "handoff-fact-drift"
    )


def test_fault_trials_run_on_isolated_stores_and_trigger_expected_faults():
    trials = run_fault_trials()
    assert len(trials) == 15
    assert all(row['failed'] for row in trials)
    for row in trials:
        if row['variant'] == 'approval_check_omitted':
            assert row['events'][0]['payload']['status'] == 'policy_denied'
        else:
            assert row['correct_quote'] == 35000 and row['proposed_quote'] == 0
