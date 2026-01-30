from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime, timezone
from enum import Enum


class VideoStatus(str, Enum):
    QUEUED = "queued"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class ErrorType(str, Enum):
    HIGH_DEMAND = "high_demand"
    PROMINENT_PEOPLE = "prominent_people"
    POLICY_VIOLATION = "policy_violation"
    NETWORK_ERROR = "network_error"
    DOWNLOAD_ERROR = "download_error"
    UNKNOWN = "unknown"


class Video(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str
    job_id: str
    
    # Source data
    image_filename: str
    prompt_number: int
    prompt_text: str
    video_index: int  # 1 or 2 (first or second output)
    
    # Generation status
    status: VideoStatus = VideoStatus.QUEUED
    generation_started_at: Optional[datetime] = None
    generation_completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    error_type: Optional[ErrorType] = None
    retry_count: int = 0
    
    # Storage URLs
    cloudflare_url: Optional[str] = None
    telegram_file_id: Optional[str] = None
    telegram_url: Optional[str] = None
    local_path_720p: Optional[str] = None
    
    # 4K upscaling
    upscaled: bool = False
    upscaled_4k_url: Optional[str] = None
    upscaled_telegram_id: Optional[str] = None
    upscale_completed_at: Optional[datetime] = None
    
    # User actions
    selected_for_download: bool = False
    downloaded: bool = False
    
    # Metadata
    duration_seconds: Optional[float] = None
    file_size_mb: Optional[float] = None
    resolution: str = "720p"
    thumbnail_url: Optional[str] = None
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class VideoResponse(BaseModel):
    video_id: str
    image_filename: str
    prompt_number: int
    prompt_text: str
    video_index: int
    status: VideoStatus
    cloudflare_url: Optional[str]
    telegram_url: Optional[str]
    upscaled: bool
    upscaled_4k_url: Optional[str]
    selected: bool
    error_message: Optional[str]
    error_type: Optional[ErrorType]
    duration_seconds: Optional[float]
    resolution: str


class VideoSelectRequest(BaseModel):
    selected: bool


class VideoRegenerateRequest(BaseModel):
    new_prompt: Optional[str] = None