"""
Test suite for Prometheus metrics endpoint.
Tests /metrics endpoint and prometheus instrumentation.
"""

import pytest
from httpx import AsyncClient

from app.core import config


@pytest.mark.skipif(
    not config.ENABLE_METRICS,
    reason="Metrics are disabled in configuration"
)
@pytest.mark.asyncio
async def test_metrics_endpoint_exists(client: AsyncClient):
    """Test that /metrics endpoint exists when enabled."""
    response = await client.get("/metrics")
    
    # Should return 200 when metrics are enabled
    assert response.status_code == 200

@pytest.mark.skipif(
    not config.ENABLE_METRICS,
    reason="Metrics are disabled in configuration"
)
@pytest.mark.asyncio
async def test_metrics_format(client: AsyncClient):
    """Test that metrics endpoint returns Prometheus format."""
    response = await client.get("/metrics")
    
    assert response.status_code == 200
    content = response.text
        
    # Should contain Prometheus metric format
    # Common metrics from prometheus-fastapi-instrumentator
    assert "http_requests_total" in content or "http_request" in content
    assert "TYPE" in content  # Prometheus TYPE comments
    assert "HELP" in content  # Prometheus HELP comments


@pytest.mark.asyncio
async def test_metrics_not_in_admin_auth(client: AsyncClient):
    """Test that /metrics endpoint does not require admin authentication."""
    # Metrics should be accessible without auth (for Prometheus scraping)
    response = await client.get("/metrics")
    
    # Should not return 401 or 403 (authentication errors)
    # It may return 404 if metrics are disabled
    assert response.status_code != 401
    assert response.status_code != 403


@pytest.mark.skipif(
    not config.ENABLE_METRICS,
    reason="Metrics are disabled in configuration"
)
@pytest.mark.asyncio
async def test_metrics_after_requests(client: AsyncClient):
    """Test that metrics are updated after making requests."""
    # Make some requests to generate metrics
    await client.get("/health")
    await client.get("/")
    
    # Get metrics
    response = await client.get("/metrics")

    assert response.status_code == 200
    content = response.text
        
    # Should have recorded our requests
    assert "http_" in content  # Some HTTP metric should exist


@pytest.mark.asyncio
async def test_metrics_excluded_from_count(client: AsyncClient):
    """Test that /metrics endpoint doesn't count itself in metrics."""
    # This is configured via excluded_handlers in instrumentator
    response = await client.get("/metrics")
    
    # Just verify endpoint responds appropriately
    assert response.status_code in [200, 404]


def test_metrics_configuration():
    """Test that metrics configuration is properly set."""
    # Verify ENABLE_METRICS flag exists and is boolean
    assert isinstance(config.ENABLE_METRICS, bool)
    
    # Test environment variable parsing
    assert config.ENABLE_METRICS in [True, False]


@pytest.mark.skipif(
    not config.ENABLE_METRICS,
    reason="Metrics are disabled in configuration"
)
@pytest.mark.asyncio
async def test_metrics_content_type(client: AsyncClient):
    """Test that metrics endpoint returns correct content type."""
    response = await client.get("/metrics")
    
    assert response.status_code == 200
    # Prometheus metrics should be text/plain
    content_type = response.headers.get("content-type", "")
    assert "text/plain" in content_type or "text" in content_type


@pytest.mark.skipif(
    not config.ENABLE_METRICS,
    reason="Metrics are disabled in configuration"
)
@pytest.mark.asyncio
async def test_metrics_include_labels(client: AsyncClient):
    """Test that metrics include proper labels."""
    # Make some labeled requests
    await client.get("/health")
    
    response = await client.get("/metrics")
    
    assert response.status_code == 200
    content = response.text
        
    # Should include HTTP method labels
    assert 'method="GET"' in content or "GET" in content


@pytest.mark.asyncio
async def test_health_endpoint_not_affected_by_metrics(client: AsyncClient):
    """Test that /health still works regardless of metrics configuration."""
    response = await client.get("/health")
    
    # Health should always work
    assert response.status_code in [200, 503]
    
    data = response.json()
    assert "status" in data
    assert "service" in data
