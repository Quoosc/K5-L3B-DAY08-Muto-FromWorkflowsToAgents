"""Host checks independent of the three student shapes.

Expected amounts are written from docs/business_rules.md, not computed by
the compensation function being tested elsewhere.
"""

import json

import pytest

from lab8.db import connect
from lab8.durability import InjectedCrash, committed_audit_count, get_refund, issue_refund
from lab8.policy import order_refunded_vnd


@pytest.mark.parametrize("approved", [0, -1])
def test_non_positive_approval_denies_retries_without_effect(public_db, approved):
    conn = connect(public_db)
    try:
        conn.execute("UPDATE approvals SET approved_vnd = ? WHERE approval_id = 'A-001'", (approved,))
        conn.commit()
        for _ in range(2):
            outcome = issue_refund(conn, "C-001", 35000)
            assert not outcome["ok"]
            assert outcome["reason"] == "non_positive_amount"
        assert get_refund(conn, "C-001") is None
        assert committed_audit_count(conn, "C-001") == 0
        rows = conn.execute(
            "SELECT details_json FROM audit_events WHERE claim_id = 'C-001' AND event_type = 'policy_denied'"
        ).fetchall()
        assert len(rows) == 1
        assert json.loads(rows[0]["details_json"])["reason"] == "non_positive_amount"
    finally:
        conn.close()


def test_dangling_approval_reference_does_not_pay(public_db):
    conn = connect(public_db)
    try:
        conn.execute("UPDATE claims SET approval_id = 'A-ABSENT' WHERE claim_id = 'C-001'")
        conn.commit()
        outcome = issue_refund(conn, "C-001", 35000)
        assert not outcome["ok"]
        assert outcome["reason"] == "missing_approval"
        assert get_refund(conn, "C-001") is None
        assert committed_audit_count(conn, "C-001") == 0
        assert conn.execute(
            "SELECT COUNT(*) FROM audit_events WHERE claim_id = 'C-001' AND event_type = 'policy_denied'"
        ).fetchone()[0] == 1
    finally:
        conn.close()


def test_paid_cap_applies_to_remaining_amount_after_prior_refund(public_db):
    conn = connect(public_db)
    try:
        # Earlier refund is 30,000. Only 70,000 of paid=100,000 remains,
        # even though the full proposal and approval are both 150,000.
        conn.execute("UPDATE orders SET paid_vnd = 100000 WHERE order_id = 'O-515'")
        conn.commit()
        outcome = issue_refund(conn, "C-014", 150000)
        assert outcome["ok"]
        assert get_refund(conn, "C-014")["amount_vnd"] == 70000
        assert order_refunded_vnd(conn, "O-515") == 100000
        assert committed_audit_count(conn, "C-014") == 1
    finally:
        conn.close()


@pytest.mark.parametrize("point", ["before_effect", "after_effect_before_checkpoint", "after_checkpoint"])
def test_topup_crash_resumes_on_new_connection_once(public_db, point):
    conn = connect(public_db)
    try:
        with pytest.raises(InjectedCrash):
            issue_refund(conn, "C-014", 150000, crash_at=point)
    finally:
        conn.close()

    # Reopen the database to model process loss, not just a retry on one connection.
    conn = connect(public_db)
    try:
        if point == "before_effect":
            assert get_refund(conn, "C-014") is None
            assert committed_audit_count(conn, "C-014") == 0
        else:
            assert get_refund(conn, "C-014")["amount_vnd"] == 120000
            assert committed_audit_count(conn, "C-014") == 1
        for _ in range(2):
            assert issue_refund(conn, "C-014", 150000)["ok"]
        assert conn.execute(
            "SELECT COUNT(*) FROM refund_ledger WHERE claim_id = 'C-014'"
        ).fetchone()[0] == 1
        assert get_refund(conn, "C-014")["amount_vnd"] == 120000
        assert order_refunded_vnd(conn, "O-515") == 150000
        assert committed_audit_count(conn, "C-014") == 1
        checkpoint = conn.execute(
            "SELECT result_json FROM checkpoints WHERE claim_id = 'C-014' AND step = 'issue_refund'"
        ).fetchone()
        assert json.loads(checkpoint["result_json"])["amount_vnd"] == 120000
    finally:
        conn.close()
