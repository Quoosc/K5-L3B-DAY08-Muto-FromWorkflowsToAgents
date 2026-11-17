from __future__ import annotations

import json
import time
from pathlib import Path

from lab8.db import connect
from lab8.shapes.single import run_claim


def test_single_agent_refund_trace_is_safe_and_host_commits(public_db):
    started_at = time.time()
    result = run_claim("C-001", seed=11, store_path=str(public_db))

    assert result.status == "resolved"
    assert result.proposal_amount == 35000
    assert result.committed_audit_count == 1
    assert len(result.refund_effects) == 1

    trace_path = Path(result.trace_path)
    trace = json.loads(trace_path.read_text(encoding="utf-8"))
    assert trace["run_id"] == result.run_id
    assert isinstance(trace["events"], list)
    assert trace_path.stat().st_mtime >= started_at - 1.0

    artifact = json.dumps(result.as_dict(), ensure_ascii=False) + trace_path.read_text(
        encoding="utf-8"
    )
    for forbidden in (
        "CANARY_SECRET_",
        "PRIVATE_PHONE",
        "PRIVATE_ADDRESS",
        "PRIVATE_NOTE",
        "PRIVATE_ITEM",
    ):
        assert forbidden not in artifact

    conn = connect(public_db)
    try:
        refund_count = conn.execute(
            "SELECT COUNT(*) AS n FROM refund_ledger WHERE claim_id = 'C-001'"
        ).fetchone()["n"]
    finally:
        conn.close()
    assert refund_count == 1


def test_single_agent_retry_keeps_one_refund_and_one_audit(public_db):
    first = run_claim("C-001", seed=11, store_path=str(public_db))
    second = run_claim("C-001", seed=11, store_path=str(public_db))

    assert first.status == "resolved"
    assert second.status == "resolved"
    assert second.refund_effects == first.refund_effects
    assert second.committed_audit_count == 1

    conn = connect(public_db)
    try:
        refund_count = conn.execute(
            "SELECT COUNT(*) AS n FROM refund_ledger WHERE claim_id = 'C-001'"
        ).fetchone()["n"]
        audit_count = conn.execute(
            """
            SELECT COUNT(*) AS n FROM audit_events
            WHERE claim_id = 'C-001' AND event_type = 'refund_committed'
            """
        ).fetchone()["n"]
    finally:
        conn.close()
    assert refund_count == 1
    assert audit_count == 1
