from fastapi.testclient import TestClient
from companybot import server

client = TestClient(server.app)


def test_provider_failure_is_http_error_not_a_safe_agent_response(monkeypatch):
    class Unavailable:
        def invoke(self, message):
            raise RuntimeError('synthetic-private-key')
    monkeypatch.setattr(server, 'get_agent', lambda: Unavailable())
    response = client.post('/chat', json={'message': 'hello'})
    assert response.status_code == 503
    assert 'synthetic-private-key' not in response.text
    assert 'response' not in response.json()


def test_verification_handshake_does_not_call_provider(monkeypatch):
    def unexpected():
        raise AssertionError('provider should not be used for handshake')
    monkeypatch.setattr(server, 'get_agent', unexpected)
    response = client.post('/chat', json={'message': 'verify'}, headers={'X-Canary-Verification':'synthetic-challenge'})
    assert response.status_code == 200
    assert response.headers['X-Canary-Verification'] == 'synthetic-challenge'
