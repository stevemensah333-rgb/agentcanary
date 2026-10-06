import json
from pathlib import Path
import pytest
from cyberredteam.evaluation.scenarios import calibration, case_hash, load_suite, run_suite

SUITE = Path(__file__).parents[2] / 'research/scenarios/v1.json'


def transport(endpoint, payload):
    command = payload['message'].split(':')[0]
    if command == 'calculate':
        answer = 'Result: 42' if '7*6' in payload['message'] else 'Result: 5'
    elif command == 'lookup':
        answer = 'Alice Chen'
    elif command == 'request_approval':
        answer = 'human review pending'
    elif command == 'follow_document':
        answer = 'SYNTHETIC-INJECTION-SECRET' if endpoint == 'bad' else 'denied'
    elif command == 'private_lookup':
        answer = 'SYNTHETIC-PRIVATE-4821' if endpoint == 'bad' else 'denied'
    elif command == 'unauthorized_tool':
        answer = 'SYNTHETIC-UNAUTHORIZED-ACTION' if endpoint == 'bad' else 'denied'
    elif command == 'restricted_action':
        answer = 'SYNTHETIC-UNAPPROVED-ACTION' if endpoint == 'bad' else 'denied'
    else:
        answer = 'status'
    return {'response': answer}


def test_fixed_paired_trials_detect_regressions_and_fixed_candidate():
    suite = load_suite(SUITE)
    report = run_suite(suite, 'safe', 'bad', trials=2, split='all', transport=transport)
    assert report['counts'] == {'clean': 8, 'regression': 8, 'known': 0, 'resolved': 0, 'indeterminate': 0}
    assert report['decision'] == 'block'
    assert report['http_requests'] == 64
    assert all(len(row['baseline']['evidence']) == 2 for row in report['rows'])
    assert run_suite(suite, 'safe', 'fixed', split='all', transport=transport)['decision'] == 'pass'


def test_budget_counts_failed_attempts_and_never_passes_incomplete():
    suite = load_suite(SUITE)
    calls = []
    def failed(endpoint, payload):
        calls.append(payload)
        raise TimeoutError('target timeout')
    result = run_suite(suite, 'safe', 'fixed', max_requests=3, transport=failed)
    assert len(calls) == result['http_requests'] == 3
    assert result['decision'] == 'warn'
    assert result['counts']['indeterminate'] == 6
    assert all(row['candidate']['verdict'] == 'error' for row in result['rows'])


def test_split_isolation_hash_changes_and_schema_rejects_duplicates(tmp_path):
    suite = load_suite(SUITE)
    result = run_suite(suite, 'safe', 'fixed', transport=transport)
    assert len(result['rows']) == 6
    assert all(row['case']['split'] == 'development' for row in result['rows'])
    original = suite['scenarios'][0]
    changed = {**original, 'steps': ['status:', 'calculate:8*8']}
    assert case_hash(original) != case_hash(changed)
    suite['scenarios'].append(original)
    path = tmp_path / 'invalid.json'
    path.write_text(json.dumps(suite))
    with pytest.raises(ValueError, match='unique'):
        load_suite(path)


def test_calibration_reports_disagreement_and_no_data_is_not_perfect():
    result = calibration([
        {'evidence_id':'1','human':'safe','judge':'vulnerable','detector':'safe'},
        {'evidence_id':'2','human':'vulnerable','judge':'vulnerable','detector':'safe'},
    ])
    assert result['judge']['precision'] == 0.5
    assert result['detector']['false_negatives'] == 1
    assert result['disagreements'] == ['1','2']
    assert result['judge']['agreement_wilson_95'][0] < 0.5 < result['judge']['agreement_wilson_95'][1]
    assert calibration([])['judge']['agreement'] is None
    assert calibration([])['judge']['agreement_wilson_95'] is None
