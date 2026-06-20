"""
Real integration test for profile update.
Tests the full flow: register -> login -> update profile -> verify.
Run: python -m pytest tests/test_profile_integration.py -v
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


@pytest.fixture
def client():
    """Create Flask test client."""
    from api.app.main import app
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def auth_token(client):
    """Register a test user and return auth token."""
    import time
    unique = str(int(time.time()))
    test_email = f"profile_test_{unique}@example.com"
    test_password = "TestPass123!"

    # Register
    reg_resp = client.post('/api/auth/register', json={
        'email': test_email,
        'password': test_password,
    }, content_type='application/json')

    # Login
    login_resp = client.post('/api/auth/login', json={
        'email': test_email,
        'password': test_password,
    }, content_type='application/json')

    data = login_resp.get_json()
    assert data.get('success'), f"Login failed: {data}"
    return {
        'token': data['token'],
        'email': test_email,
        'password': test_password,
    }


class TestProfileUpdateIntegration:
    """Real API tests for profile update."""

    def test_get_profile_returns_name(self, client, auth_token):
        """GET /api/profile should return name field."""
        resp = client.get('/api/profile', headers={
            'Authorization': f"Bearer {auth_token['token']}"
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'profile' in data
        assert 'name' in data['profile'], "Profile response missing 'name'"

    def test_update_profile_with_name(self, client, auth_token):
        """PUT /api/profile with name should update successfully."""
        new_name = "TestUserUpdated"
        resp = client.put('/api/profile', json={
            'name': new_name,
            'email': auth_token['email'],
        }, headers={
            'Authorization': f"Bearer {auth_token['token']}",
            'Content-Type': 'application/json',
        })

        assert resp.status_code == 200
        data = resp.get_json()
        assert data['message'] == 'Profile updated successfully'
        assert data['profile']['name'] == new_name

    def test_update_profile_name_persists(self, client, auth_token):
        """Updated name should persist on subsequent GET."""
        new_name = "PersistentName"
        client.put('/api/profile', json={
            'name': new_name,
            'email': auth_token['email'],
        }, headers={
            'Authorization': f"Bearer {auth_token['token']}",
            'Content-Type': 'application/json',
        })

        # GET and verify
        resp = client.get('/api/profile', headers={
            'Authorization': f"Bearer {auth_token['token']}"
        })
        data = resp.get_json()
        assert data['profile']['name'] == new_name

    def test_update_profile_short_name_rejected(self, client, auth_token):
        """Name shorter than 2 chars should be rejected."""
        resp = client.put('/api/profile', json={
            'name': 'A',
            'email': auth_token['email'],
        }, headers={
            'Authorization': f"Bearer {auth_token['token']}",
            'Content-Type': 'application/json',
        })

        assert resp.status_code == 400
        data = resp.get_json()
        assert 'error' in data

    def test_update_profile_without_auth_rejected(self, client):
        """PUT /api/profile without token should return 401."""
        resp = client.put('/api/profile', json={
            'name': 'NoAuth',
            'email': 'test@test.com',
        }, headers={
            'Content-Type': 'application/json',
        })

        assert resp.status_code in [401, 403]

    def test_profile_to_dict_includes_name(self, client, auth_token):
        """Profile to_dict() must include name field."""
        resp = client.get('/api/profile', headers={
            'Authorization': f"Bearer {auth_token['token']}"
        })
        data = resp.get_json()
        profile = data['profile']
        assert 'name' in profile
        assert isinstance(profile['name'], str) or profile['name'] is None
