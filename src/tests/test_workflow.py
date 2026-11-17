"""Shape A regressions beyond the provided public matrix."""

import json
from pathlib import Path

import pytest

from lab8.db import connect
from lab8.durability import InjectedCrash
from lab8.shapes.workflow import run_claim


def test_workflow_unknown_claim_has_fresh_trace(public_db):
    result = run_claim("C-UNKNOWN", seed=11, store_path=str(public_db))
    assert result.status == "failed"
    assert result.error_reason == "unknown_claim"
    assert result.refund_effects == []
    trace = json.loads(Path(result.trace_path).read_text(encoding="utf-8"))
    assert trace["run_id"] == result.run_id
    assert trace["events"]


def test_workflow_does_not_trace_ticket_or_private_order_data(public_db, capsys):
    conn = connect(public_db)
    private = ["CANARY_SECRET_TICKET", "PRIVATE_PHONE", "PRIVATE_ADDRESS", "PRIVATE_NOTE", "PRIVATE_ITEM"]
    conn.execute("UPDATE claims SET ticket = ? WHERE claim_id = 'C-001'", (private[0],))
    conn.execute(
        "UPDATE orders SET phone = ?, address = ?, internal_note = ?, item_name = ? WHERE order_id = 'O-107'",
        private[1:],
    )
    conn.commit()
    conn.close()
    result = run_claim("C-001", seed=55, store_path=str(public_db))
    captured = capsys.readouterr()
    blob = json.dumps(result.as_dict()) + Path(result.trace_path).read_text(encoding="utf-8")
    blob += captured.out + captured.err
    assert result.status == "resolved"
    assert all(value not in blob for value in private)
    assert "CANARY_SECRET_" not in blob


@pytest.mark.parametrize("point", ["before_effect", "after_effect_before_checkpoint", "after_checkpoint"])
def test_workflow_resume_at_each_crash_window(public_db, point):
    with pytest.raises(InjectedCrash):
        run_claim("C-001", seed=11, store_path=str(public_db), crash_at=point)
    result = run_claim("C-001", seed=11, store_path=str(public_db))
    assert result.status == "resolved"
    assert len(result.refund_effects) == 1
    assert result.refund_effects[0]["amount_vnd"] == 35000
    assert result.committed_audit_count == 1


def test_workflow_borrowed_approval_denied_with_audit(public_db):
    conn = connect(public_db)
    conn.execute("UPDATE claims SET approval_id = 'A-001' WHERE claim_id = 'C-014'")
    conn.commit()
    conn.close()
    result = run_claim("C-014", seed=11, store_path=str(public_db))
    assert result.status == "denied"
    assert result.proposal_amount == 150000
    assert result.error_reason == "approval_claim_mismatch"
    assert result.refund_effects == []
    conn = connect(public_db)
    try:
        assert conn.execute(
            "SELECT COUNT(*) FROM audit_events WHERE claim_id = 'C-014' AND event_type = 'policy_denied'"
        ).fetchone()[0] == 1
    finally:
        conn.close()


def test_workflow_conflict_preserves_committed_refund(public_db):
    first = run_claim("C-001", seed=11, store_path=str(public_db))
    conn = connect(public_db)
    conn.execute("UPDATE orders SET shipping_fee_vnd = 10000 WHERE order_id = 'O-107'")
    conn.commit()
    conn.close()
    second = run_claim("C-001", seed=11, store_path=str(public_db))
    assert first.status == "resolved"
    assert second.status == "failed"
    assert second.error_reason == "amount_conflict"
    assert second.proposal_amount == 10000
    assert second.refund_effects == first.refund_effects
    assert second.committed_audit_count == 1
