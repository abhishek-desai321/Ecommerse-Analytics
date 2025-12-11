from fastapi import FastAPI, HTTPException, Request, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
import uuid
import logging
from .schemas import EventCreate, MetricResponse
from .redis_client import redis_client
from .config import settings


# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI(title="Real-time Analytics API")

Instrumentator(should_group_status_codes=False).instrument(app).expose(app, endpoint="/prometheus")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate Limiter Dependency
async def rate_limiter(request: Request):
    client_ip = request.client.host
    # Simple fixed window: 50 reqs / sec per IP
    # Implementation: Use Redis key `rate_limit:<ip>:<second>`
    current_second = int(time.time())
    key = f"rate_limit:{client_ip}:{current_second}"
    
    # Pipeline: INCR and EXPIRE
    pipe = redis_client.redis.pipeline()
    pipe.incr(key)
    pipe.expire(key, 5) # Expire after 5s to be safe
    result = await pipe.execute()
    
    count = result[0]
    if count > settings.RATE_LIMIT_PER_SECOND: # Limit to configured reqs/sec per IP
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded"
        )

from fastapi.exceptions import RequestValidationError

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle validation errors: 
    1. Log error
    2. Push raw body to DLQ
    3. Return 422
    """
    try:
        body = await request.body()
        body_str = body.decode("utf-8")
        
        # Structure for DLQ
        dlq_data = {
            "error": str(exc),
            "body": body_str,
            "ip": request.client.host,
            "timestamp": str(int(time.time()))
        }
        
        await redis_client.add_dlq_event(dlq_data)
        logger.warning(f"Validation error captured to DLQ: {exc}")
        
    except Exception as e:
        logger.error(f"Error handling validation exception: {e}")
        
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "body": exc.body},
    )

@app.on_event("shutdown")
async def shutdown_event():
    await redis_client.close()

@app.post("/ingest", status_code=status.HTTP_202_ACCEPTED)
async def ingest_event(event: EventCreate, _ = Depends(rate_limiter)):
    """
    Accepts JSON events -> Validates -> Pushes to Redis Stream
    """
    # Create event payload
    event_data = event.model_dump(mode='json')
    # Convert all values to strings for Redis Stream
    redis_data = {k: str(v) for k, v in event_data.items()}

    try:
        await redis_client.add_event(redis_data)
        return {"status": "accepted", "id": str(uuid.uuid4())}
    except Exception as e:
        logger.error(f"Error ingesting event: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get("/metrics", response_model=MetricResponse)
async def get_metrics():
    """
    Reads active metrics from Redis
    """
    try:
        active_users = await redis_client.get_active_users()
        active_sessions = await redis_client.get_active_sessions()
        top_pages = await redis_client.get_top_pages(5)
        avg_sessions = await redis_client.get_avg_sessions_active_user()

        return MetricResponse(
            active_users=active_users,
            active_sessions=active_sessions,
            avg_sessions_per_user=avg_sessions,
            top_pages=top_pages
        )
    except Exception as e:
        logger.error(f"Error fetching metrics: {e}")
        raise HTTPException(status_code=500, detail="Error fetching metrics")

@app.get("/users/active")
async def get_active_users_list():
    """
    Get list of currently active user IDs
    """
    try:
        users = await redis_client.get_active_user_ids()
        return {"users": users}
    except Exception as e:
        logger.error(f"Error fetching active users: {e}")
        raise HTTPException(status_code=500, detail="Error fetching active users")

@app.get("/users/{user_id}/sessions")
async def get_user_sessions(user_id: str):
    """
    Get active session count for a specific user
    """
    try:
        count = await redis_client.get_user_session_count(user_id)
        return {"user_id": user_id, "active_sessions": count}
    except Exception as e:
        logger.error(f"Error fetching user sessions: {e}")
        raise HTTPException(status_code=500, detail="Error fetching user sessions")
