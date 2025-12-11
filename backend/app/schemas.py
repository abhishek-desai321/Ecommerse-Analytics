from pydantic import BaseModel, ConfigDict
from datetime import datetime

class EventCreate(BaseModel):
    event_type: str
    page_url: str
    user_id: str
    session_id: str
    timestamp: datetime # ISO 8601 string or datetime object

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "timestamp": "2024-03-15T14:30:00Z",
                "user_id": "usr_789",
                "event_type": "page_view",
                "page_url": "/products/electronics",
                "session_id": "sess_456"
            }
        }
    )

class MetricResponse(BaseModel):
    active_users: int
    active_sessions: int
    avg_sessions_per_user: float
    top_pages: dict[str, int]
