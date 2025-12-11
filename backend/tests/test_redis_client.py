import pytest
from app.redis_client import RedisClient

# We need a running Redis for integration tests, or mock it.
# Since we are running in docker, we might have access to redis service.
# For unit tests, it is better to mock redis.asyncio.Redis
from unittest.mock import AsyncMock, patch, MagicMock

@pytest.mark.asyncio
async def test_get_active_users():
    with patch("redis.asyncio.from_url") as mock_redis_cls:
        mock_redis = AsyncMock()
        mock_redis_cls.return_value = mock_redis
        
        client = RedisClient()
        mock_redis.zcard.return_value = 42
        
        count = await client.get_active_users()
        assert count == 42
        mock_redis.zcard.assert_called_with("analytics:active_users")

@pytest.mark.asyncio
async def test_get_top_pages():
    with patch("redis.asyncio.from_url") as mock_redis_cls:
        mock_redis = AsyncMock()
        mock_redis_cls.return_value = mock_redis
        
        # Mock Pipeline
        mock_pipeline = MagicMock()
        # KEY FIX: pipeline method is sync
        mock_redis.pipeline = MagicMock(return_value=mock_pipeline)
        # hgetall is called on the pipeline object, so it should be a method on the mock_pipeline
        # It adds to buffer and returns self (not awaitable)
        mock_pipeline.hgetall.return_value = mock_pipeline

        # Mock execute result
        # It returns a list of dictionaries (buckets)
        mock_pipeline.execute = AsyncMock(return_value=[
            {"url1": "10", "url2": "5"},
            {"url1": "2", "url3": "1"}
        ])

        client = RedisClient()      
        pages = await client.get_top_pages(limit=5)
        assert pages == {"url1": 12, "url2": 5, "url3": 1}
