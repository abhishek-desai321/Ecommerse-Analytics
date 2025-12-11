import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.main import app
from unittest.mock import AsyncMock, patch, MagicMock

@pytest.mark.asyncio
async def test_ingest_event():
    # Mock redis add_event directly on the imported object in main
    with patch("app.main.redis_client", new_callable=AsyncMock) as mock_redis:
        # Fix pipeline mock
        # pipeline() is synchronous, returns a Pipeline object
        mock_pipeline = MagicMock() 
        mock_pipeline.incr.return_value = mock_pipeline
        mock_pipeline.expire.return_value = mock_pipeline
        mock_pipeline.execute = AsyncMock(return_value=[1]) # execute is async
        
        # KEY FIX: The pipeline *method* itself must be a MagicMock (sync), not AsyncMock
        mock_redis.redis.pipeline = MagicMock(return_value=mock_pipeline)
        
        mock_redis.add_event = AsyncMock()
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post("/ingest", json={
                "event_type": "page_view",
                "page_url": "http://example.com",
                "user_id": "test_user",
                "session_id": "test_session",
                "timestamp": "2024-03-15T12:00:00Z"
            })
        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "accepted"
        assert "id" in data

@pytest.mark.asyncio
async def test_get_metrics_empty():
    # Mock redis_client methods
    with patch("app.main.redis_client") as mock_redis:
        mock_redis.get_active_users = AsyncMock(return_value=0)
        mock_redis.get_active_sessions = AsyncMock(return_value=0)
        mock_redis.get_avg_sessions_active_user = AsyncMock(return_value=0.0)
        mock_redis.get_top_pages = AsyncMock(return_value={})
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get("/metrics")
        
        assert response.status_code == 200
        data = response.json()
        assert data["active_users"] == 0
        assert data["active_sessions"] == 0
        assert data["top_pages"] == {}
