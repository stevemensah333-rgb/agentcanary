from datetime import datetime, timedelta
from fastapi.testclient import TestClient
import pytest
from cyberredteam.api import app, require_auth, settings
from cyberredteam.release_gate import create_project, create_release
from cyberredteam.security.tokens import issue_project_token
from cyberredteam.storage.artifact_store import SQLiteStore
from cyberredteam.storage.models import ProjectTokenRecord, ProjectRecord


@pytest.fixture
def scoped_api(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, 'db_path', tmp_path / 'tokens.db')
    monkeypatch.setattr(settings, 'database_url', None)
    monkeypatch.setattr(settings, 'api_secret_key', 'administrator-test-key')
    app.dependency_overrides.pop(require_auth, None)
    store = SQLiteStore(settings.database_location)
    with store.SessionLocal() as session:
        own = create_project(session, {'name':'own','repository':'stevemensah333-rgb/agentcanary','endpoint':'https://owned.example.test/chat'})
        foreign = create_project(session, {'name':'other','repository':'stevemensah333-rgb/other-fixture','endpoint':'https://other.example.test/chat'})
        own_release = create_release(session, own, 'abcd1234', 'preview')
        other_release = create_release(session, foreign, 'abcd5678', 'preview')
        own_release.status = other_release.status = 'completed'
        own_release.decision = other_release.decision = 'warn'
        tokens = {}
        for name, scopes in [('full',['release:create','release:read']),('create',['release:create']),('read',['release:read']),('none',[])]:
            issued = issue_project_token(pepper=settings.token_pepper)
            session.add(ProjectTokenRecord(token_id=name,project_id=own.project_id,lookup_prefix=issued.lookup_prefix,token_hash=issued.token_hash,scopes=scopes))
            tokens[name] = {'Authorization':'Bearer ' + issued.token}
        session.commit()
        values = (own.project_id, own_release.release_id, other_release.release_id, tokens)
    try:
        yield TestClient(app), store, values
    finally:
        app.dependency_overrides[require_auth] = lambda: None
        store.close()


def test_action_can_poll_own_release_and_reports_only(scoped_api):
    client, store, (_, own, other, tokens) = scoped_api
    assert client.get('/api/releases/' + own, headers=tokens['full']).status_code == 200
    assert client.get('/api/releases/' + own + '/regressions', headers=tokens['read']).status_code == 200
    assert client.get('/api/releases/' + own + '/report', headers=tokens['read']).status_code == 200
    assert client.get('/api/releases/' + own + '/report.md', headers=tokens['read']).status_code == 200
    assert client.get('/api/releases/' + other, headers=tokens['full']).status_code == 403
    assert client.get('/api/releases/' + own, headers=tokens['create']).status_code == 403
    assert client.get('/api/projects', headers=tokens['full']).status_code == 403
    assert client.get('/api/telemetry/llm-calls', headers=tokens['full']).status_code == 403
    with store.SessionLocal() as session:
        session.get(ProjectTokenRecord, 'full').revoked_at = datetime.utcnow()
        session.get(ProjectTokenRecord, 'read').expires_at = datetime.utcnow() - timedelta(minutes=1)
        session.commit()
    assert client.get('/api/releases/' + own, headers=tokens['full']).status_code == 401
    assert client.get('/api/releases/' + own, headers=tokens['read']).status_code == 401


def test_cross_project_create_is_rejected_before_any_contract_mutation(scoped_api):
    client, store, (_, _, _, tokens) = scoped_api
    request = {'repository':'stevemensah333-rgb/other-fixture','commit_sha':'abcd1234','endpoint':'https://changed.example.test/chat','verification_token':'synthetic-fixture-verification-token'}
    response = client.post('/api/ci/releases', json=request, headers=tokens['full'])
    assert response.status_code == 403
    with store.SessionLocal() as session:
        from sqlalchemy import select
        project = session.scalar(select(ProjectRecord).where(ProjectRecord.repository == 'stevemensah333-rgb/other-fixture'))
        assert project.endpoint == 'https://other.example.test/chat'
    assert client.post('/api/ci/releases', json=request, headers=tokens['read']).status_code == 403


def test_administrator_can_register_repository_binding(scoped_api, monkeypatch):
    client, store, values = scoped_api
    monkeypatch.setattr('cyberredteam.api._validate_target_contract', lambda endpoint, template: None)
    result = client.post('/api/projects', json={'name':'new binding','repository':'stevemensah333-rgb/NEW-FIXTURE','endpoint':'https://owned.example.test/chat'}, headers={'Authorization':'Bearer administrator-test-key'})
    assert result.status_code == 201
    assert result.json()['repository'] == 'stevemensah333-rgb/new-fixture'
