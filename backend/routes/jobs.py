from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks
from typing import List, Optional
import logging
from pathlib import Path
import shutil
import aiofiles
import asyncio

from models.job import JobCreate, Job, JobResponse, JobListItem, JobStatus
from services.database_service import db_service
from services.video_processor import video_processor
from services.google_flow_service import google_flow_service
from config import TEMP_UPLOAD_DIR

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/create", response_model=JobResponse)
async def create_job(job_data: JobCreate):
    """
    Create a new video generation job
    """
    try:
        job = await db_service.create_job(job_data.job_name)
        
        return JobResponse(
            job_id=job.id,
            job_name=job.job_name,
            status=job.status,
            progress=0.0,
            total_images=0,
            current_image=0,
            completed_videos=0,
            failed_videos=0,
            expected_videos=0,
            created_at=job.created_at,
            updated_at=job.updated_at
        )
    except Exception as e:
        logger.error(f"Failed to create job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{job_id}/upload")
async def upload_files(
    job_id: str,
    images_folder: UploadFile = File(...),
    prompts_file: UploadFile = File(...)
):
    """
    Upload images folder (zip) and prompts file
    """
    try:
        # Get job
        job = await db_service.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Create job directory
        job_dir = TEMP_UPLOAD_DIR / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        
        # Save images zip
        images_zip_path = job_dir / "images.zip"
        async with aiofiles.open(images_zip_path, 'wb') as f:
            content = await images_folder.read()
            await f.write(content)
        
        # Extract images
        images_folder_path = job_dir / "images"
        images_folder_path.mkdir(exist_ok=True)
        extracted_path = video_processor.extract_zip(images_zip_path, images_folder_path)
        
        # Save prompts file
        prompts_file_path = job_dir / "prompts.txt"
        async with aiofiles.open(prompts_file_path, 'wb') as f:
            content = await prompts_file.read()
            await f.write(content)
        
        # Parse files
        images_dict = video_processor.extract_images_from_folder(extracted_path)
        prompts_dict = video_processor.parse_prompts_file(prompts_file_path)
        
        # Validate
        is_valid, error_msg = video_processor.validate_inputs(images_dict, prompts_dict)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Update job
        total_images = len(images_dict)
        expected_videos = total_images * 2  # 2 outputs per prompt
        
        await db_service.update_job(job_id, {
            "total_images": total_images,
            "total_prompts": len(prompts_dict),
            "expected_videos": expected_videos,
            "images_folder_path": str(extracted_path),
            "prompts_file_path": str(prompts_file_path)
        })
        
        # Create video records
        await video_processor.create_video_records(job_id, images_dict, prompts_dict)
        
        logger.info(f"Uploaded files for job {job_id}: {total_images} images, {expected_videos} expected videos")
        
        return {
            "uploaded": True,
            "image_count": total_images,
            "prompt_count": len(prompts_dict),
            "expected_videos": expected_videos
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload files: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{job_id}", response_model=JobResponse)
async def get_job_status(job_id: str):
    """
    Get job status and progress
    """
    try:
        job = await db_service.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Calculate progress
        progress = 0.0
        if job.expected_videos > 0:
            progress = job.completed_videos / job.expected_videos
        
        return JobResponse(
            job_id=job.id,
            job_name=job.job_name,
            status=job.status,
            progress=progress,
            total_images=job.total_images,
            current_image=job.current_processing,
            completed_videos=job.completed_videos,
            failed_videos=job.failed_videos,
            expected_videos=job.expected_videos,
            created_at=job.created_at,
            updated_at=job.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=List[JobListItem])
async def list_jobs(status: Optional[JobStatus] = None, limit: int = 50):
    """
    List all jobs with optional status filter
    """
    try:
        jobs = await db_service.list_jobs(status, limit)
        
        result = []
        for job in jobs:
            progress = 0.0
            if job.expected_videos > 0:
                progress = job.completed_videos / job.expected_videos
            
            result.append(JobListItem(
                job_id=job.id,
                job_name=job.job_name,
                status=job.status,
                progress=progress,
                completed_videos=job.completed_videos,
                expected_videos=job.expected_videos,
                created_at=job.created_at
            ))
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to list jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{job_id}/start")
async def start_job(job_id: str, background_tasks: BackgroundTasks):
    """
    Start the automation process for a job
    Runs video generation in background
    """
    try:
        # Get job
        job = await db_service.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Check if files are uploaded
        if not job.images_folder_path or not job.prompts_file_path:
            raise HTTPException(status_code=400, detail="Please upload images and prompts first")
        
        # Check if already processing
        if job.status == JobStatus.PROCESSING:
            return {"message": "Job is already processing", "started": False}
        
        # Start background task
        background_tasks.add_task(
            google_flow_service.generate_videos_for_job,
            job_id
        )
        
        # Estimate time (rough estimate: 5 minutes per image)
        estimated_minutes = job.total_images * 5
        
        logger.info(f"Started automation for job {job_id}")
        
        return {
            "started": True,
            "estimated_time_minutes": estimated_minutes,
            "message": f"Video generation started for {job.total_images} images"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{job_id}")
async def delete_job(job_id: str):
    """
    Delete job and all associated data
    """
    try:
        # Delete from database
        deleted = await db_service.delete_job(job_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Delete local files
        job_dir = TEMP_UPLOAD_DIR / job_id
        if job_dir.exists():
            shutil.rmtree(job_dir)
        
        logger.info(f"Deleted job {job_id}")
        return {"deleted": True}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete job: {e}")
        raise HTTPException(status_code=500, detail=str(e))