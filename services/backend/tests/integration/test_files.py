import pytest

@pytest.mark.asyncio
async def test_health_check(client):
    """Test health check endpoint"""
    test_client = await client
    response = test_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
