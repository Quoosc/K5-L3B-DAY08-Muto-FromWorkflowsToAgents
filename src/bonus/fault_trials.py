"""Run three deliberate faults against lab quote/host, with isolated SQLite stores."""
from __future__ import annotations

import copy
import json
import tempfile
from pathlib import Path

from lab8.compensation import quote
from lab8.db import init_store
from lab8.durability import issue_refund
from lab8.tools import get_claim_view, lookup_order, lookup_policy


def run_fault_trials() -> list[dict]:
    world = json.loads(Path('data/public_world_state.json').read_text(encoding='utf-8'))
    claims = [json.loads(line) for line in Path('data/public_claims.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]
    cases = []
    with tempfile.TemporaryDirectory(prefix='b2-fault-') as temp:
        for variant, claim_id in [('handoff_drops_delay', 'C-001'), ('stale_policy_clause', 'C-001'), ('approval_check_omitted', 'C-007')]:
            for seed in (11, 22, 33, 44, 55):
                conn = init_store(Path(temp) / f'{variant}-{seed}.sqlite', world, claims)
                try:
                    claim = get_claim_view(conn, claim_id)
                    order = lookup_order(conn, claim['order_id'], claim['principal_id'])['order']
                    policies = lookup_policy(conn)['policies']
                    correct = quote(order, policies, as_of=world['as_of']).amount_vnd
                    events = []
                    if variant == 'handoff_drops_delay':
                        altered = dict(order, delay_days=0)
                        proposed = quote(altered, policies, as_of=world['as_of']).amount_vnd
                        events = [{'kind': 'investigator', 'payload': {'lookup_order': {'order': {'delay_days': order['delay_days']}}}},
                                  {'kind': 'worker_decision', 'payload': {'delay_days': altered['delay_days']}}]
                        failed = proposed != correct
                    elif variant == 'stale_policy_clause':
                        stale = copy.deepcopy(policies)
                        stale[0]['clauses'] = [dict(stale[0]['clauses'][0], min_delay_days=99)]
                        proposed = quote(order, stale, as_of=world['as_of']).amount_vnd
                        events = [{'kind': 'policy_selection', 'payload': {'as_of': world['as_of'],
                                  'selected_clause': {'clause_id': 'OLD-LATE', 'expires_at': '2026-01-01'}}}]
                        failed = proposed != correct
                    else:
                        proposed = correct
                        outcome = issue_refund(conn, claim_id, proposed)
                        events = [{'kind': 'host_outcome', 'payload': {'status': 'policy_denied' if not outcome['ok'] else 'committed', 'reason': outcome['reason']}}]
                        failed = not outcome['ok']
                    cases.append({'case_id': f'{variant}-{seed}', 'variant': variant, 'claim_id': claim_id,
                                  'seed': seed, 'correct_quote': correct, 'proposed_quote': proposed,
                                  'failed': failed, 'events': events})
                finally:
                    conn.close()
    return cases
