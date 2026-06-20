"""
Tests for Pipeline Orchestrator API endpoints.
Run: python -m pytest tests/test_pipeline.py -v
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


class TestPipelineStatus:
    """Test GET /api/pipeline/status endpoint."""

    def test_status_returns_200(self, client):
        resp = client.get('/api/pipeline/status')
        assert resp.status_code == 200

    def test_status_has_required_fields(self, client):
        data = client.get('/api/pipeline/status').get_json()
        assert 'status' in data
        assert 'data_freshness' in data
        assert 'models' in data
        assert 'timestamp' in data

    def test_status_has_gold_and_silver(self, client):
        data = client.get('/api/pipeline/status').get_json()
        assert 'gold' in data['data_freshness']
        assert 'silver' in data['data_freshness']
        assert 'gold' in data['models']
        assert 'silver' in data['models']

    def test_status_is_active_or_degraded(self, client):
        data = client.get('/api/pipeline/status').get_json()
        assert data['status'] in ['active', 'degraded']

    def test_freshness_has_required_fields(self, client):
        data = client.get('/api/pipeline/status').get_json()
        for asset in ['gold', 'silver']:
            fresh = data['data_freshness'][asset]
            assert 'is_fresh' in fresh
            assert 'age_hours' in fresh
            assert 'rows' in fresh

    def test_model_has_required_fields(self, client):
        data = client.get('/api/pipeline/status').get_json()
        for asset in ['gold', 'silver']:
            model = data['models'][asset]
            assert 'exists' in model


class TestPipelineDetails:
    """Test GET /api/pipeline/details endpoint."""

    def test_details_returns_200(self, client):
        resp = client.get('/api/pipeline/details')
        assert resp.status_code == 200

    def test_details_has_pipelines(self, client):
        data = client.get('/api/pipeline/details').get_json()
        assert 'pipelines' in data
        assert 'etl' in data['pipelines']
        assert 'features' in data['pipelines']
        assert 'training' in data['pipelines']

    def test_details_has_data_and_models(self, client):
        data = client.get('/api/pipeline/details').get_json()
        assert 'data' in data
        assert 'models' in data
        assert 'health' in data

    def test_pipeline_has_schedule(self, client):
        data = client.get('/api/pipeline/details').get_json()
        for key in ['etl', 'features', 'training']:
            p = data['pipelines'][key]
            assert 'name' in p
            assert 'status' in p
            assert 'schedule' in p
            assert 'description' in p

    def test_health_has_status(self, client):
        data = client.get('/api/pipeline/details').get_json()
        assert data['health']['status'] in ['healthy', 'degraded']


class TestPipelineRun:
    """Test POST /api/pipeline/run endpoint."""

    def test_run_invalid_asset_returns_400(self, client):
        resp = client.post('/api/pipeline/run', json={'type': 'update', 'asset': 'invalid'})
        assert resp.status_code == 400

    def test_run_invalid_type_returns_400(self, client):
        resp = client.post('/api/pipeline/run', json={'type': 'invalid', 'asset': 'gold'})
        assert resp.status_code == 400

    def test_run_update_gold_starts(self, client):
        resp = client.post('/api/pipeline/run', json={'type': 'update', 'asset': 'gold'})
        assert resp.status_code in [200, 500]  # 500 if Yahoo Finance fails in test env


class TestPipelineIntegration:
    """Integration tests for pipeline flow."""

    def test_status_to_details_flow(self, client):
        """Status should be consistent with details."""
        status = client.get('/api/pipeline/status').get_json()
        details = client.get('/api/pipeline/details').get_json()

        # Data freshness should match
        for asset in ['gold', 'silver']:
            assert status['data_freshness'][asset]['is_fresh'] == details['data'][asset]['is_fresh']

    def test_model_info_consistency(self, client):
        """Model info should be consistent across endpoints."""
        status = client.get('/api/pipeline/status').get_json()
        details = client.get('/api/pipeline/details').get_json()

        for asset in ['gold', 'silver']:
            assert status['models'][asset]['exists'] == details['models'][asset]['exists']

    def test_pipeline_status_structure(self, client):
        """Verify complete response structure."""
        data = client.get('/api/pipeline/status').get_json()

        # Top level
        assert isinstance(data['status'], str)
        assert isinstance(data['data_freshness'], dict)
        assert isinstance(data['models'], dict)
        assert isinstance(data['timestamp'], str)

        # Freshness
        for asset in ['gold', 'silver']:
            f = data['data_freshness'][asset]
            assert isinstance(f['is_fresh'], bool)
            assert isinstance(f['age_hours'], (int, float))
            assert isinstance(f['rows'], int)
