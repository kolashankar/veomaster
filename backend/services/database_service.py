from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import uuid
import logging
from config import MONGO_URL, DB_NAME
from models.job import Job, JobStatus
from models.video import Video, VideoStatus
from models.session import GoogleFlowSession

logger = logging.getLogger(__name__)


class DatabaseService:
    def __init__(self):
        self.client = AsyncIOMotorClient(MONGO_URL)
        self.db = self.client[DB_NAME]
        self.jobs_collection = self.db.jobs
        self.videos_collection = self.db.videos
        self.sessions_collection = self.db.google_flow_sessions
    
    # =============== JOB OPERATIONS ===============
    
    async def create_job(self, job_name: str) -> Job:
        """Create a new automation job"""
        job_id = str(uuid.uuid4())
        job = Job(
            id=job_id,
            job_name=job_name,
            status=JobStatus.PENDING
        )
        
        doc = job.model_dump()
        doc['created_at'] = doc['created_at'].isoformat()
        doc['updated_at'] = doc['updated_at'].isoformat()
        
        await self.jobs_collection.insert_one(doc)
        logger.info(f"Created job: {job_id} - {job_name}")
        return job
    
    async def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID"""
        doc = await self.jobs_collection.find_one({"id": job_id}, {"_id": 0})
        if not doc:
            return None
        
        # Convert ISO strings back to datetime
        doc['created_at'] = datetime.fromisoformat(doc['created_at'])
        doc['updated_at'] = datetime.fromisoformat(doc['updated_at'])
        
        return Job(**doc)
    
    async def update_job(self, job_id: str, updates: Dict[str, Any]) -> bool:
        """Update job fields"""
        updates['updated_at'] = datetime.now(timezone.utc).isoformat()
        
        result = await self.jobs_collection.update_one(
            {"id": job_id},
            {"$set": updates}
        )
        return result.modified_count > 0
    
    async def list_jobs(self, status: Optional[JobStatus] = None, limit: int = 50) -> List[Job]:
        """List jobs with optional status filter"""
        query = {}
        if status:
            query['status'] = status.value
        
        cursor = self.jobs_collection.find(query, {"_id": 0}).sort("created_at", -1).limit(limit)
        docs = await cursor.to_list(length=limit)
        
        jobs = []
        for doc in docs:
            doc['created_at'] = datetime.fromisoformat(doc['created_at'])
            doc['updated_at'] = datetime.fromisoformat(doc['updated_at'])
            jobs.append(Job(**doc))
        
        return jobs
    
    async def delete_job(self, job_id: str) -> bool:
        """Delete job and all associated videos"""
        # Delete videos first
        await self.videos_collection.delete_many({"job_id": job_id})
        
        # Delete job
        result = await self.jobs_collection.delete_one({"id": job_id})
        logger.info(f"Deleted job: {job_id}")
        return result.deleted_count > 0
    
    # =============== VIDEO OPERATIONS ===============
    
    async def create_video(self, video: Video) -> Video:
        """Create a new video record"""
        doc = video.model_dump()
        doc['created_at'] = doc['created_at'].isoformat()
        
        # Convert datetime fields to ISO strings
        if doc.get('generation_started_at'):
            doc['generation_started_at'] = doc['generation_started_at'].isoformat()
        if doc.get('generation_completed_at'):
            doc['generation_completed_at'] = doc['generation_completed_at'].isoformat()
        if doc.get('upscale_completed_at'):
            doc['upscale_completed_at'] = doc['upscale_completed_at'].isoformat()
        
        await self.videos_collection.insert_one(doc)
        logger.info(f"Created video: {video.id} for job {video.job_id}")
        return video
    
    async def get_video(self, video_id: str) -> Optional[Video]:
        """Get video by ID"""
        doc = await self.videos_collection.find_one({"id": video_id}, {"_id": 0})
        if not doc:
            return None
        
        # Convert ISO strings back to datetime
        doc['created_at'] = datetime.fromisoformat(doc['created_at'])
        if doc.get('generation_started_at'):
            doc['generation_started_at'] = datetime.fromisoformat(doc['generation_started_at'])
        if doc.get('generation_completed_at'):
            doc['generation_completed_at'] = datetime.fromisoformat(doc['generation_completed_at'])
        if doc.get('upscale_completed_at'):
            doc['upscale_completed_at'] = datetime.fromisoformat(doc['upscale_completed_at'])
        
        return Video(**doc)
    
    async def update_video(self, video_id: str, updates: Dict[str, Any]) -> bool:
        """Update video fields"""
        # Convert datetime objects to ISO strings
        for key in ['generation_started_at', 'generation_completed_at', 'upscale_completed_at']:
            if key in updates and isinstance(updates[key], datetime):
                updates[key] = updates[key].isoformat()
        
        result = await self.videos_collection.update_one(
            {"id": video_id},
            {"$set": updates}
        )
        return result.modified_count > 0
    
    async def get_job_videos(self, job_id: str) -> List[Video]:
        """Get all videos for a job"""
        cursor = self.videos_collection.find({"job_id": job_id}, {"_id": 0}).sort("prompt_number", 1)
        docs = await cursor.to_list(length=1000)
        
        videos = []
        for doc in docs:
            doc['created_at'] = datetime.fromisoformat(doc['created_at'])
            if doc.get('generation_started_at'):
                doc['generation_started_at'] = datetime.fromisoformat(doc['generation_started_at'])
            if doc.get('generation_completed_at'):
                doc['generation_completed_at'] = datetime.fromisoformat(doc['generation_completed_at'])
            if doc.get('upscale_completed_at'):
                doc['upscale_completed_at'] = datetime.fromisoformat(doc['upscale_completed_at'])
            videos.append(Video(**doc))
        
        return videos
    
    async def get_selected_videos(self, job_id: str) -> List[Video]:
        """Get all selected videos for a job"""
        cursor = self.videos_collection.find(
            {"job_id": job_id, "selected_for_download": True},
            {"_id": 0}
        )
        docs = await cursor.to_list(length=1000)
        
        videos = []
        for doc in docs:
            doc['created_at'] = datetime.fromisoformat(doc['created_at'])
            if doc.get('generation_started_at'):
                doc['generation_started_at'] = datetime.fromisoformat(doc['generation_started_at'])
            if doc.get('generation_completed_at'):
                doc['generation_completed_at'] = datetime.fromisoformat(doc['generation_completed_at'])
            if doc.get('upscale_completed_at'):
                doc['upscale_completed_at'] = datetime.fromisoformat(doc['upscale_completed_at'])
            videos.append(Video(**doc))
        
        return videos
    
    # =============== SESSION OPERATIONS ===============
    
    async def get_session(self) -> Optional[GoogleFlowSession]:
        """Get Google Flow session (singleton)"""
        doc = await self.sessions_collection.find_one({"id": "google_flow_session"}, {"_id": 0})
        if not doc:
            return None
        
        # Convert ISO strings back to datetime
        if doc.get('last_login_at'):
            doc['last_login_at'] = datetime.fromisoformat(doc['last_login_at'])
        if doc.get('last_used_at'):
            doc['last_used_at'] = datetime.fromisoformat(doc['last_used_at'])
        
        return GoogleFlowSession(**doc)
    
    async def save_session(self, session: GoogleFlowSession) -> bool:
        """Save or update Google Flow session"""
        doc = session.model_dump()
        
        # Convert datetime to ISO strings
        if doc.get('last_login_at'):
            doc['last_login_at'] = doc['last_login_at'].isoformat()
        if doc.get('last_used_at'):
            doc['last_used_at'] = doc['last_used_at'].isoformat()
        
        result = await self.sessions_collection.update_one(
            {"id": "google_flow_session"},
            {"$set": doc},
            upsert=True
        )
        return result.acknowledged
    
    async def close(self):
        """Close database connection"""
        self.client.close()


# Singleton instance
db_service = DatabaseService()