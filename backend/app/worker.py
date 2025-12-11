import asyncio
import logging
import time
import json
from .config import settings
from .redis_client import redis_client
from prometheus_client import start_http_server, Counter, Gauge

# Prometheus Metrics
EVENTS_PROCESSED = Counter('events_processed_total', 'Total number of events processed', ['status', 'event_type'])
PROCESSING_ERRORS = Counter('processing_errors_total', 'Total number of errors during event processing')
ACTIVE_USERS = Gauge('active_users', 'Number of active users in the last 5 minutes')
ACTIVE_SESSIONS = Gauge('active_sessions', 'Number of active sessions in the last 5 minutes')

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_consumer_group():
    try:
        await redis_client.redis.xgroup_create(
            settings.STREAM_KEY,
            settings.CONSUMER_GROUP,
            id="0",
            mkstream=True
        )
        logger.info(f"Created consumer group {settings.CONSUMER_GROUP}")
    except Exception as e:
        if "BUSYGROUP" in str(e):
            logger.info("Consumer group already exists")
        else:
            logger.error(f"Error creating consumer group: {e}")

async def process_event(event_id, event_data):
    """
    Update metrics in Redis sorted sets.
    """
    try:
        # Check event_data format. Redis returns byte keys/values or strings depending on client.
        # We used decode_responses=True in redis_client, so they are strings.
        
        # Parse ISO timestamp to float
        ts_str = event_data.get("timestamp")
        if ts_str:
            try:
                # Use fromisoformat for python 3.7+
                from datetime import datetime
                dt = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                timestamp = dt.timestamp()
            except Exception:
                timestamp = time.time()
        else:
            timestamp = time.time()

        user_id = event_data.get("user_id")
        session_id = event_data.get("session_id")
        page_url = event_data.get("page_url")
        event_type = event_data.get("event_type")
        
        pipe = redis_client.redis.pipeline()
        
        # 1. Active Users (Last 5 mins)
        if user_id:
             # Score = timestamp, Member = user_id
             pipe.zadd("analytics:active_users", {user_id: timestamp})
             
        # 2. Page Views (Last 15 mins)
        if page_url and event_type == "page_view":
            # OPTIMIZATION: Time Buckets
            # Instead of storing every single event in a ZSET (O(N) memory),
            # we aggregate counts into small 1-minute buckets (O(buckets * pages) memory).
            
            # Calculate bucket timestamp (floor to nearest minute)
            bucket_ts = int(timestamp // 60) * 60
            bucket_key = f"analytics:views:{bucket_ts}"
            
            # Increment count for this page in this bucket
            pipe.hincrby(bucket_key, page_url, 1)
            
            # Set expiry for this bucket (window + 5 mins buffer). 
            pipe.expire(bucket_key, settings.WINDOW_PAGE_VIEWS + 300)

        if session_id:
            pipe.zadd("analytics:sessions", {session_id: timestamp})
            # Also store in per-user set if user_id is known
            if user_id:
                 # Key: analytics:user_sessions:<user_id>
                 # We need to prune this too. Pruning every user key is expensive in a loop.
                 # But we can set a TTL on it every time we write.
                 u_key = f"analytics:user_sessions:{user_id}"
                 pipe.zadd(u_key, {session_id: timestamp})
                 # Window is 5 mins (300s) + 5 mins buffer
                 pipe.expire(u_key, settings.WINDOW_SESSIONS + 300)

        await pipe.execute()
        
        # Metric: Success
        EVENTS_PROCESSED.labels(status="success", event_type=event_type or "unknown").inc()
        
        return True
    except Exception as e:
        logger.error(f"Error processing event {event_id}: {e}")
        PROCESSING_ERRORS.inc()
        EVENTS_PROCESSED.labels(status="error", event_type=event_type or "unknown").inc()
        return False

async def prune_old_data():
    """
    Periodically remove old entries from running ZSETs.
    This can be done in the same loop or separate task.
    """
    while True:
        try:
            now = time.time()
            
            pipe = redis_client.redis.pipeline()
            
            # Prune Active Users (< now - 300s)
            pipe.zremrangebyscore("analytics:active_users", "-inf", now - settings.WINDOW_ACTIVE_USERS)
            
            # Prune Sessions (< now - 300s)
            pipe.zremrangebyscore("analytics:sessions", "-inf", now - settings.WINDOW_SESSIONS)
            
            await pipe.execute()
            
            # Update Gauges
            try:
                users_count = await redis_client.get_active_users()
                sessions_count = await redis_client.get_active_sessions()
                ACTIVE_USERS.set(users_count)
                ACTIVE_SESSIONS.set(sessions_count)
            except Exception as e:
                logger.error(f"Error updating gauges: {e}")
            
        except Exception as e:
            logger.error(f"Error pruning data: {e}")
            
        await asyncio.sleep(5) # Prune every 5 seconds

async def consume_loop():
    # Start Prometheus Metrics Server
    start_http_server(8001)
    logger.info("Prometheus metrics server started on port 8001")
    
    await create_consumer_group()
    
    # Start pruning task
    asyncio.create_task(prune_old_data())
    
    logger.info("Starting consumer loop...")
    while True:
        try:
            # XREADGROUP
            # Count 10 max
            entries = await redis_client.redis.xreadgroup(
                settings.CONSUMER_GROUP,
                settings.CONSUMER_NAME,
                {settings.STREAM_KEY: ">"},
                count=10,
                block=2000 # 2 sec block
            )
            
            if not entries:
                continue
                
            for stream, messages in entries:
                for message_id, message_data in messages:
                    success = await process_event(message_id, message_data)
                    if success:
                        await redis_client.redis.xack(
                            settings.STREAM_KEY,
                            settings.CONSUMER_GROUP,
                            message_id
                        )

        except Exception as e:
            logger.error(f"Error in consumer loop: {e}")
            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(consume_loop())
