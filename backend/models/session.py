from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone


class GoogleFlowSession(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = "google_flow_session"  # Singleton
    session_active: bool = False
    cookies: List[Dict[str, Any]] = Field(default_factory=list)
    user_agent: Optional[str] = None
    last_login_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    login_email: str = "Sameer@techhub.codes"
    login_password: str = "Hhub@#11"  # In production, use encrypted storage


class SessionStatus(BaseModel):
    active: bool
    last_used: Optional[datetime]
    needs_login: bool