"""Check the ablation's independent business outcomes and isolation."""

import json

import pytest

from lab8.ablation_r1 import run_claim
from lab8.durability import InjectedCrash
from lab8.shapes import orchestrator


@pytest.mark.parametrize(
    "claim_id,status,proposal,effect,tool_calls",
    [("C-001", "resolved", 35000, 35000, 4),
     ("C-004", "needs_info", 0, 0, 1)],
)
def test_order_only_known_outcome_and_identity(
    public_db, claim_id, status, proposal, effect, tool_calls
):
    original_handoff = orchestrator.make_handoff
    original_id = orchestrator.make_run_id
    result = run_claim(claim_id, seed=11, store_path=str(public_db))
    assert result.shape == "r1_order_only"
    assert result.run_id == f"R-r1_order_only-{claim_id}-s11"
    assert result.status == status
    assert result.proposal_amount == proposal
    assert sum(row["amount_vnd"] for row in result.refund_effects) == effect
    assert result.committed_audit_count == int(effect > 0)
    assert result.tool_calls == tool_calls
    with open(result.trace_path, encoding="utf-8") as stream:
        trace = json.load(stream)
    assert trace["run_id"] == result.run_id
    assert orchestrator.make_handoff is original_handoff
    assert orchestrator.make_run_id is original_id


def test_crash_restores_original_shape_and_resume_is_idempotent(public_db):
    original_handoff = orchestrator.make_handoff
    original_id = orchestrator.make_run_id
    with pytest.raises(InjectedCrash):
        run_claim("C-001", seed=11, store_path=str(public_db),
                  crash_at="after_effect_before_checkpoint")
    assert orchestrator.make_handoff is original_handoff
    assert orchestrator.make_run_id is original_id
    for _ in range(2):
        result = run_claim("C-001", seed=11, store_path=str(public_db))
        assert result.status == "resolved"
        assert len(result.refund_effects) == 1
        assert result.refund_effects[0]["amount_vnd"] == 35000
        assert result.committed_audit_count == 1
