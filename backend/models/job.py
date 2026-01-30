from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime, timezone
from enum import Enum


class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobCreate(BaseModel):
    job_name: str = Field(..., min_length=1, max_length=200)


class Job(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str
    job_name: str
    status: JobStatus = JobStatus.PENDING
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Counts
    total_images: int = 0
    total_prompts: int = 0
    expected_videos: int = 0  # total_images * 2
    completed_videos: int = 0
    failed_videos: int = 0
    current_processing: int = 0  # Current image index
    
    # File paths
    images_folder_path: Optional[str] = None
    prompts_file_path: Optional[str] = None
    
    # Error tracking
    error_summary: List[str] = Field(default_factory=list)


class JobResponse(BaseModel):
    job_id: str
    job_name: str
    status: JobStatus
    progress: float = 0.0  # 0.0 to 1.0
    total_images: int
    current_image: int
    completed_videos: int
    failed_videos: int
    expected_videos: int
    created_at: datetime
    updated_at: datetime


class JobListItem(BaseModel):
    job_id: str
    job_name: str
    status: JobStatus
    progress: float
    completed_videos: int
    expected_videos: int
    created_at: datetime