from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum


class UpscaleTaskStatus(str, Enum):
    """Status of upscaling task"""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class UpscaleTask(BaseModel):
    """Model for tracking upscale tasks"""
    task_id: str
    video_ids: List[str]
    quality: str
    status: UpscaleTaskStatus = UpscaleTaskStatus.QUEUED
    progress: float = 0.0  # 0-100
    current_video_index: int = 0
    current_video_id: Optional[str] = None
    total_videos: int
    completed_videos: int = 0
    failed_videos: int = 0
    error_message: Optional[str] = None
    logs: List[Dict] = []  # List of {timestamp, message, type}
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UpscaleTaskResponse(BaseModel):
    """Response model for upscale task status"""
    task_id: str
    status: UpscaleTaskStatus
    progress: float
    current_video_index: int
    total_videos: int
    completed_videos: int
    failed_videos: int
    error_message: Optional[str] = None
    logs: List[Dict] = []
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
