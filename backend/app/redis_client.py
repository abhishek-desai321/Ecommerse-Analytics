import redis.asyncio as redis
from .config import settings

class RedisClient:
    def __init__(self):
        self.redis = redis.from_url(settings.REDIS_URL, decode_responses=True)

    async def close(self):
        await self.redis.close()

    async def add_event(self, event_data: dict) -> str:
        """Add event to Redis Stream"""
        return await self.redis.xadd(settings.STREAM_KEY, event_data)

    async def add_dlq_event(self, event_data: dict) -> str:
        """Add invalid event to DLQ Stream"""
        return await self.redis.xadd(settings.DLQ_STREAM_KEY, event_data)

    async def get_active_users(self) -> int:
        """Count users in the active window"""
        # We use ZCARD because we prune old members actively/periodically
        return await self.redis.zcard("analytics:active_users")

    async def get_active_sessions(self) -> int:
        """Count sessions in the active window"""
        return await self.redis.zcard("analytics:sessions")

    async def get_top_pages(self, limit: int = 5) -> dict[str, int]:
        """Get top pages by view count in the active window"""
        # OPTIMIZATION: Time Buckets
        # We read the last N 1-minute buckets and sum them up.
        # This is strictly O(buckets) which is very small (15 keys).
        
        now = __import__("time").time()
        current_minute = int(now // 60) * 60
        
        # Window is 15 mins. Generate keys for [now-15m, ..., now]
        # We include current minute and going back 15 mins.
        keys = []
        for i in range(16): # 0 to 15
            ts = current_minute - (i * 60)
            keys.append(f"analytics:views:{ts}")
            
        # Pipeline fetching all buckets
        pipe = self.redis.pipeline()
        for key in keys:
            pipe.hgetall(key)
        
        results = await pipe.execute()
        
        # Aggregate counts locally
        counts = {}
        for bucket_data in results:
            if not bucket_data:
                continue
            for url, count in bucket_data.items():
                counts[url] = counts.get(url, 0) + int(count)
            
        # Sort and return top limit
        sorted_pages = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:limit]
        return dict(sorted_pages)

    async def get_user_session_count(self, user_id: str) -> int:
        """Get active session count for a specific user"""
        key = f"analytics:user_sessions:{user_id}"
        # Prune lazily or just count valid ones?
        # ZCOUNT with score filter is safest.
        now = __import__("time").time()
        start_window = now - settings.WINDOW_SESSIONS
        return await self.redis.zcount(key, start_window, "+inf")

    async def get_avg_sessions_active_user(self) -> float:
        """Calculate average active sessions per active user"""
        # Note: This is global average.
        active_users = await self.get_active_users()
        active_sessions = await self.get_active_sessions()
        
        if active_users == 0:
            return 0.0
        return round(active_sessions / active_users, 2)

    async def get_active_user_ids(self) -> list[str]:
        """Get list of active user IDs"""
        # Fetch members from active_users sorted set
        # Pruning happens in worker/periodically. We assume set is reasonably up to date.
        # Fetch all
        now = __import__("time").time()
        start_window = now - settings.WINDOW_ACTIVE_USERS
        return await self.redis.zrangebyscore("analytics:active_users", start_window, "+inf")

redis_client = RedisClient()
