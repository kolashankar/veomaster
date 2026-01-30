import asyncio
import logging
from typing import Dict, Optional
from datetime import datetime, timezone
import uuid

from models.upscale_task import UpscaleTask, UpscaleTaskStatus, UpscaleTaskResponse

logger = logging.getLogger(__name__)


class TaskManager:
    """Manager for tracking upscaling tasks"""
    
    def __init__(self):
        self.tasks: Dict[str, UpscaleTask] = {}
        logger.info("TaskManager initialized")
    
    def create_task(self, video_ids: list, quality: str) -> str:
        """Create a new upscaling task"""
        task_id = str(uuid.uuid4())
        task = UpscaleTask(
            task_id=task_id,
            video_ids=video_ids,
            quality=quality,
            status=UpscaleTaskStatus.QUEUED,
            total_videos=len(video_ids),
            created_at=datetime.now(timezone.utc)
        )
        self.tasks[task_id] = task
        logger.info(f"Created upscale task {task_id} for {len(video_ids)} videos")
        return task_id
    
    def get_task(self, task_id: str) -> Optional[UpscaleTask]:
        """Get task by ID"""
        return self.tasks.get(task_id)
    
    def update_task_status(self, task_id: str, status: UpscaleTaskStatus):
        """Update task status"""
        if task_id in self.tasks:
            self.tasks[task_id].status = status
            if status == UpscaleTaskStatus.PROCESSING and not self.tasks[task_id].started_at:
                self.tasks[task_id].started_at = datetime.now(timezone.utc)
            elif status in [UpscaleTaskStatus.COMPLETED, UpscaleTaskStatus.FAILED]:
                self.tasks[task_id].completed_at = datetime.now(timezone.utc)
    
    def update_task_progress(
        self,
        task_id: str,
        progress: float,
        current_video_index: int,
        current_video_id: Optional[str] = None
    ):
        """Update task progress"""
        if task_id in self.tasks:
            self.tasks[task_id].progress = progress
            self.tasks[task_id].current_video_index = current_video_index
            if current_video_id:
                self.tasks[task_id].current_video_id = current_video_id
    
    def add_task_log(self, task_id: str, message: str, log_type: str = "info"):
        """Add log entry to task"""
        if task_id in self.tasks:
            timestamp = datetime.now(timezone.utc).isoformat()
            log_entry = {
                "timestamp": timestamp,
                "message": message,
                "type": log_type
            }
            self.tasks[task_id].logs.append(log_entry)
            logger.info(f"[Task {task_id}] {message}")
    
    def increment_completed(self, task_id: str):
        """Increment completed videos count"""
        if task_id in self.tasks:
            self.tasks[task_id].completed_videos += 1
    
    def increment_failed(self, task_id: str):
        """Increment failed videos count"""
        if task_id in self.tasks:
            self.tasks[task_id].failed_videos += 1
    
    def set_error(self, task_id: str, error_message: str):
        """Set error message for task"""
        if task_id in self.tasks:
            self.tasks[task_id].error_message = error_message
            self.add_task_log(task_id, f"Error: {error_message}", "error")
    
    def get_task_response(self, task_id: str) -> Optional[UpscaleTaskResponse]:
        """Get task as response model"""
        task = self.get_task(task_id)
        if not task:
            return None
        
        return UpscaleTaskResponse(
            task_id=task.task_id,
            status=task.status,
            progress=task.progress,
            current_video_index=task.current_video_index,
            total_videos=task.total_videos,
            completed_videos=task.completed_videos,
            failed_videos=task.failed_videos,
            error_message=task.error_message,
            logs=task.logs,
            created_at=task.created_at.isoformat(),
            started_at=task.started_at.isoformat() if task.started_at else None,
            completed_at=task.completed_at.isoformat() if task.completed_at else None
        )
    
    def cleanup_old_tasks(self, max_age_hours: int = 24):
        """Clean up old completed tasks"""
        now = datetime.now(timezone.utc)
        to_remove = []
        
        for task_id, task in self.tasks.items():
            if task.status in [UpscaleTaskStatus.COMPLETED, UpscaleTaskStatus.FAILED]:
                if task.completed_at:
                    age = (now - task.completed_at).total_seconds() / 3600
                    if age > max_age_hours:
                        to_remove.append(task_id)
        
        for task_id in to_remove:
            del self.tasks[task_id]
            logger.info(f"Cleaned up old task {task_id}")


# Singleton instance
task_manager = TaskManager()
