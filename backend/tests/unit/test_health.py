"""
Tests for health and readiness endpoints.
"""
import pytest
from httpx import AsyncClient


class TestHealthEndpoints:
    """Tests for /health and /ready endpoints."""

    @pytest.mark.asyncio
    async def test_health_endpoint(self, client: AsyncClient):
        """Test liveness probe endpoint."""
        response = await client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "aquanexis-backend"
        assert "version" in data
        assert "timestamp" in data

    @pytest.mark.asyncio
    async def test_readiness_endpoint(self, client: AsyncClient):
        """Test readiness probe endpoint."""
        response = await client.get("/ready")
        # Should be 200 if DB is ready, 503 if not
        assert response.status_code in (200, 503)

        data = response.json()
        assert "ready" in data
        assert "timestamp" in data
        assert "checks" in data
        assert isinstance(data["checks"], list)

        # Check structure of checks
        for check in data["checks"]:
            assert "name" in check
            assert "healthy" in check
            assert "message" in check

    @pytest.mark.asyncio
    async def test_detailed_health_endpoint(self, client: AsyncClient):
        """Test detailed health endpoint."""
        response = await client.get("/health/detailed")
        assert response.status_code == 200

        data = response.json()
        assert data["service"] == "aquanexis-backend"
        assert "database" in data
        assert "settings" in data
        assert "timestamp" in data

    @pytest.mark.asyncio
    async def test_root_endpoint(self, client: AsyncClient):
        """Test root endpoint."""
        response = await client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert data["service"] == "AquaNexis API"
        assert "version" in data
        assert data["status"] == "running"

    @pytest.mark.asyncio
    async def test_metrics_endpoint(self, client: AsyncClient):
        """Test Prometheus metrics endpoint."""
        response = await client.get("/metrics")
        assert response.status_code == 200
        assert "http_requests_total" in response.text
        assert "http_request_duration_seconds" in response.text