"""Persist real fixture HTTP evidence via the existing release domain.

Only for the local integration demo. Does not run the production LLM graph.
"""
import argparse
import json
import uuid
from pathlib import Path
from sqlalchemy.orm import sessionmaker
from cyberredteam.release_gate import create_project, create_release, accept_baseline, build_differential_pairs, finalise_differential_release, release_payload
from cyberredteam.storage.models import init_db, RunRecord, AttackRecord


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', type=Path, required=True)
    parser.add_argument('reports', type=Path, nargs='+')
    args = parser.parse_args()
    reports = [json.loads(path.read_text()) for path in args.reports]
    # Never accept arbitrary/model evidence as fixture-derived evidence.
    for report in reports:
        if report['trials'] != 1 or report['counts']['indeterminate']:
            raise ValueError('Demo import requires a complete single-trial report')
        for row in report['rows']:
            for role in ['baseline','candidate']:
                if row[role]['status'] != 'completed' or any(e['response'].get('mode') != 'integration-fixture' for e in row[role]['evidence']):
                    raise ValueError('Demo import accepts only completed fixture evidence')
    engine = init_db(str(args.database))
    try:
        with sessionmaker(bind=engine)() as session:
            project = create_project(session, {'name': 'Local integration fixture (not an LLM evaluation)', 'endpoint': reports[0]['endpoints']['candidate'], 'environment': 'local-fixture', 'strategies': ['tool_misuse','sensitive_data_exposure','indirect_injection','workflow_manipulation']})
            mapping = {'unauthorized_tool_use':'tool_misuse','synthetic_data_leakage':'sensitive_data_exposure','indirect_prompt_injection':'indirect_injection','failed_human_escalation':'workflow_manipulation'}
            def persist(report, role):
                run_id = 'fixture-' + uuid.uuid4().hex
                session.add(RunRecord(run_id=run_id, target_id=report['endpoints'][role], status='completed', total_attacks=len(report['rows'])))
                session.flush()
                for index, row in enumerate(report['rows']):
                    verdict = row[role]
                    vulnerable = verdict['verdict'] == 'vulnerable'
                    session.add(AttackRecord(run_id=run_id, target_id=report['endpoints'][role], attempt_number=index+1, strategy_type=mapping[row['case']['category']], technique_id=row['scenario_id'], prompt=json.dumps(row['case']['steps']), response=json.dumps(verdict['evidence']), success=int(vulnerable), severity='high' if vulnerable else 'info', score=1.0 if vulnerable else 0.0, indicators={'deterministic_hits':verdict['hits'], 'fixture_only':True, 'case_hash':row['case_hash']}))
                session.commit()
                return run_id
            baseline = create_release(session, project, 'fixture-baseline-v1', 'local-fixture')
            baseline.run_id = persist(reports[0], 'baseline')
            baseline.status = 'completed'
            baseline.decision = 'warn'
            session.commit()
            accept_baseline(session, baseline.release_id, 'explicit-local-fixture-demo')
            summaries = []
            for index, report in enumerate(reports):
                release = create_release(session, project, f'fixture-candidate-{index}', 'local-fixture')
                release.run_id = persist(report, 'candidate')
                release.baseline_replay_run_id = persist(report, 'baseline')
                session.commit()
                pairs, coverage = build_differential_pairs(session, project, release)
                finalise_differential_release(session, release, project, pairs, coverage)
                assert release.decision == report['decision'], (release.decision, report['decision'])
                summaries.append({'release_id':release.release_id,'decision':release.decision})
            print(json.dumps({'project_id':project.project_id,'releases':summaries}))
    finally:
        engine.dispose()


if __name__ == '__main__':
    main()
