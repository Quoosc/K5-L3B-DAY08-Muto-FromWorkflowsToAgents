"""Role 3 tests: orchestrator handoff allowlist, trace contract v1, and secret/PII safety."""

from __future__ import annotations

import json
import time

import pytest

from lab8.db import connect, init_store
from lab8.durability import InjectedCrash
from lab8.handoff import ALLOWED_FIELDS, READONLY_TOOLS, WRITE_TOOLS, HandoffError, make_handoff
from lab8.metrics import artifact_blob, check_trace, ledger_snapshot
from lab8.shapes import SHAPES
from lab8.shapes.orchestrator import run_claim
from tests.conftest import BY_ID, CLAIMS, WORLD

# Add "workflow" here once workflow.py is implemented to audit all three shapes.
SHAPES_READY_FOR_TRACE_AUDIT = ["orchestrator", "single", "workflow"]


def test_make_handoff_strips_unknown_facts_and_blocks_canary_or_write_tools():
    cleaned = make_handoff(
        request_id="REQ-1",
        claim_id="C-001",
        task="investigate",
        facts={"delay_days": 4, "parent_secret": "CANARY_SECRET_PARENT_C-001", "raw_headers": "x"},
        allowed_tools=["lookup_order", "lookup_refund_history"],
    )
    assert set(cleaned) <= ALLOWED_FIELDS
    assert cleaned["facts"] == {"delay_days": 4}
    assert "CANARY_SECRET_" not in json.dumps(cleaned)

    with pytest.raises(HandoffError):
        make_handoff(
            request_id="REQ-2",
            claim_id="C-001",
            task="investigate",
            facts={"carrier": "CANARY_SECRET_PARENT_C-001"},
            allowed_tools=["lookup_order"],
        )

    with pytest.raises(HandoffError):
        make_handoff(
            request_id="REQ-3",
            claim_id="C-001",
            task="write",
            facts={},
            allowed_tools=["append_audit"],
        )


def test_orchestrator_handoff_trace_is_sanitized_and_readonly(public_db):
    started = time.time()
    result = run_claim("C-010", seed=11, store_path=str(public_db)).as_dict()
    assert check_trace(result, started_at=started) == (True, "ok")

    trace_body = json.loads(open(result["trace_path"], encoding="utf-8").read())
    handoff_events = [ev["payload"] for ev in trace_body["events"] if ev["kind"] == "handoff"]
    assert len(handoff_events) == 1
    handoff = handoff_events[0]
    assert handoff["contract_version"] == "handoff.v1"
    assert set(handoff) <= ALLOWED_FIELDS
    assert set(handoff["allowed_tools"]) <= READONLY_TOOLS
    assert not (set(handoff["allowed_tools"]) & WRITE_TOOLS)

    blob = artifact_blob(result)
    for token in BY_ID["C-010"]["expected"]["forbid_substrings"]:
        assert token not in blob


@pytest.mark.parametrize("shape", SHAPES_READY_FOR_TRACE_AUDIT)
@pytest.mark.parametrize(
    ("claim_id", "expected_status"),
    [
        ("C-001", "resolved"),
        ("C-002", "denied"),
        ("C-004", "needs_info"),
        ("C-005", "escalated"),
        ("C-007", "denied"),
        ("C-UNKNOWN", "failed"),
    ],
)
def test_implemented_shapes_write_clean_trace_on_all_branches(
    tmp_path, capsys, shape, claim_id, expected_status
):
    store = tmp_path / f"{shape}-{claim_id}.sqlite"
    init_store(store, WORLD, CLAIMS).close()

    started = time.time()
    result = SHAPES[shape](claim_id, seed=11, store_path=str(store)).as_dict()
    captured = capsys.readouterr()

    assert result["status"] == expected_status
    assert check_trace(result, started_at=started) == (True, "ok")

    blob = artifact_blob(result) + "\n" + captured.out + "\n" + captured.err
    assert "CANARY_SECRET_" not in blob
    assert "Bearer " not in blob
    if claim_id in BY_ID:
        for token in BY_ID[claim_id]["expected"].get("forbid_substrings", []):
            assert token not in blob


def test_orchestrator_rejects_mismatched_approval_and_audits_policy_denied(tmp_path):
    store = tmp_path / "orch-mismatch.sqlite"
    conn = init_store(store, WORLD, CLAIMS)
    try:
        conn.execute(
            """
            INSERT INTO claims (claim_id, principal_id, order_id, ticket, parent_secret, raw_headers_json, approval_id)
            VALUES (
                'C-MISMATCH',
                'P-100',
                'O-107',
                'Đơn trễ 4 ngày',
                'CANARY_SECRET_PARENT_C-MISMATCH',
                '{"Authorization": "Bearer CANARY_SECRET_PARENT_C-MISMATCH"}',
                'A-001'
            )
            """
        )
        conn.commit()
    finally:
        conn.close()

    started = time.time()
    result = run_claim("C-MISMATCH", seed=11, store_path=str(store)).as_dict()
    assert result["status"] == "denied"
    assert result["proposal_amount"] == 35000
    assert check_trace(result, started_at=started) == (True, "ok")
    assert "CANARY_SECRET_PARENT_C-MISMATCH" not in artifact_blob(result)

    conn = connect(store)
    try:
        snap = ledger_snapshot(conn, "C-MISMATCH")
    finally:
        conn.close()
    assert snap["refund_count"] == 0
    assert snap["committed_audit_count"] == 0
    assert snap["policy_denied"] is True


@pytest.mark.parametrize("crash_point", ["before_effect", "after_effect_before_checkpoint"])
def test_orchestrator_crash_flushes_clean_trace_and_resumes_once(tmp_path, crash_point):
    store = tmp_path / f"orch-crash-{crash_point}.sqlite"
    init_store(store, WORLD, CLAIMS).close()

    started = time.time()
    with pytest.raises(InjectedCrash):
        run_claim(
            "C-012",
            seed=11,
            store_path=str(store),
            crash_at=crash_point,
        )

    resumed = run_claim("C-012", seed=11, store_path=str(store)).as_dict()
    assert resumed["status"] == "resolved"
    assert resumed["proposal_amount"] == 35000
    assert check_trace(resumed, started_at=started) == (True, "ok")
    assert "CANARY_SECRET_" not in artifact_blob(resumed)

    conn = connect(store)
    try:
        snap = ledger_snapshot(conn, "C-012")
    finally:
        conn.close()
    assert snap["refund_count"] == 1
    assert snap["refund_vnd"] == 35000
    assert snap["committed_audit_count"] == 1
