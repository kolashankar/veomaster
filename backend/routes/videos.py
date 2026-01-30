from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from typing import List
import logging
from pathlib import Path
import zipfile
import io
from pydantic import BaseModel

from models.video import VideoResponse, VideoSelectRequest, VideoStatus, ErrorType
from models.upscale_task import UpscaleTaskResponse
from services.database_service import db_service
from services.upscaler_service import upscaler_service
from services.storage_service import StorageService
from services.task_manager import task_manager
from config import TEMP_DOWNLOAD_DIR

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/videos", tags=["videos"])
storage_service = StorageService()


# Request models
class UpscaleRequest(BaseModel):
    video_ids: List[str]
    quality: str = "balanced"  # fast, balanced, high


class DownloadRequest(BaseModel):
    video_ids: List[str]
    folder_name: str = "videos"
    resolution: str = "720p"  # 720p or 4K


class RegenerateRequest(BaseModel):
    new_prompt: str = None
    # In future, could add image upload support here


@router.get("/job/{job_id}", response_model=List[VideoResponse])
async def get_job_videos(job_id: str):
    """
    Get all videos for a job
    """
    try:
        videos = await db_service.get_job_videos(job_id)
        
        result = []
        for video in videos:
            result.append(VideoResponse(
                video_id=video.id,
                image_filename=video.image_filename,
                prompt_number=video.prompt_number,
                prompt_text=video.prompt_text,
                video_index=video.video_index,
                status=video.status,
                cloudflare_url=video.cloudflare_url,
                telegram_url=video.telegram_url,
                upscaled=video.upscaled,
                upscaled_4k_url=video.upscaled_4k_url,
                selected=video.selected_for_download,
                error_message=video.error_message,
                error_type=video.error_type,
                duration_seconds=video.duration_seconds,
                resolution=video.resolution
            ))
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to get job videos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{video_id}/select")
async def toggle_video_selection(video_id: str, request: VideoSelectRequest):
    """
    Toggle video selection for download
    """
    try:
        video = await db_service.get_video(video_id)
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")
        
        await db_service.update_video(video_id, {
            "selected_for_download": request.selected
        })
        
        return {"updated": True, "selected": request.selected}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update video selection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{video_id}", response_model=VideoResponse)
async def get_video(video_id: str):
    """
    Get single video details
    """
    try:
        video = await db_service.get_video(video_id)
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")
        
        return VideoResponse(
            video_id=video.id,
            image_filename=video.image_filename,
            prompt_number=video.prompt_number,
            prompt_text=video.prompt_text,
            video_index=video.video_index,
            status=video.status,
            cloudflare_url=video.cloudflare_url,
            telegram_url=video.telegram_url,
            upscaled=video.upscaled,
            upscaled_4k_url=video.upscaled_4k_url,
            selected=video.selected_for_download,
            error_message=video.error_message,
            error_type=video.error_type,
            duration_seconds=video.duration_seconds,
            resolution=video.resolution
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get video: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upscale")
async def upscale_videos(request: UpscaleRequest, background_tasks: BackgroundTasks):
    """
    Trigger 4K upscaling for selected videos
    Runs in background with progress tracking
    """
    try:
        if not request.video_ids:
            raise HTTPException(status_code=400, detail="No videos selected")
        
        # Validate quality preset
        if request.quality not in ['fast', 'balanced', 'high']:
            raise HTTPException(status_code=400, detail="Invalid quality preset. Choose: fast, balanced, or high")
        
        # Validate videos exist
        for video_id in request.video_ids:
            video = await db_service.get_video(video_id)
            if not video:
                raise HTTPException(status_code=404, detail=f"Video {video_id} not found")
            if video.status != VideoStatus.COMPLETED:
                raise HTTPException(status_code=400, detail=f"Video {video_id} is not completed yet")
        
        # Create task for tracking
        task_id = task_manager.create_task(request.video_ids, request.quality)
        
        # Start upscaling in background
        background_tasks.add_task(
            upscaler_service.upscale_videos_batch,
            request.video_ids,
            request.quality,
            task_id
        )
        
        logger.info(f"Started upscaling {len(request.video_ids)} videos with '{request.quality}' quality (task_id: {task_id})")
        
        return {
            "started": True,
            "task_id": task_id,
            "video_count": len(request.video_ids),
            "quality": request.quality,
            "message": "Upscaling started in background"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start upscaling: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/upscale/status/{task_id}", response_model=UpscaleTaskResponse)
async def get_upscale_status(task_id: str):
    """
    Get status of an upscaling task
    """
    try:
        task = task_manager.get_task_response(task_id)
        if not task:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        
        return task
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/download")
async def download_videos(request: DownloadRequest):
    """
    Download selected videos as a ZIP file
    """
    try:
        if not request.video_ids:
            raise HTTPException(status_code=400, detail="No videos selected")
        
        logger.info(f"Preparing download of {len(request.video_ids)} videos in {request.resolution}")
        
        # Create zip file in memory
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for video_id in request.video_ids:
                video = await db_service.get_video(video_id)
                if not video:
                    logger.warning(f"Video {video_id} not found, skipping")
                    continue
                
                # Determine which URL to use
                if request.resolution == "4K" and video.upscaled:
                    # Download 4K version
                    if video.upscaled_telegram_id:
                        temp_path = TEMP_DOWNLOAD_DIR / f"{video_id}_4k_temp.mp4"
                        success = await storage_service.download_from_telegram(
                            video.upscaled_telegram_id,
                            temp_path
                        )
                        if success and temp_path.exists():
                            filename = f"{video.prompt_number}_{video.video_index}_4K.mp4"
                            zip_file.write(str(temp_path), filename)
                            temp_path.unlink()  # Clean up
                elif video.status == VideoStatus.COMPLETED:
                    # Download 720p version
                    if video.local_path_720p and Path(video.local_path_720p).exists():
                        # Use local file
                        filename = f"{video.prompt_number}_{video.video_index}_720p.mp4"
                        zip_file.write(video.local_path_720p, filename)
                    elif video.telegram_file_id:
                        # Download from Telegram
                        temp_path = TEMP_DOWNLOAD_DIR / f"{video_id}_temp.mp4"
                        success = await storage_service.download_from_telegram(
                            video.telegram_file_id,
                            temp_path
                        )
                        if success and temp_path.exists():
                            filename = f"{video.prompt_number}_{video.video_index}_720p.mp4"
                            zip_file.write(str(temp_path), filename)
                            temp_path.unlink()  # Clean up
        
        # Prepare zip for streaming
        zip_buffer.seek(0)
        
        logger.info(f"✅ ZIP file created for download: {request.folder_name}.zip")
        
        # Return as streaming response
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="{request.folder_name}.zip"'
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create download: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@router.post("/{video_id}/regenerate")
async def regenerate_video(video_id: str, request: RegenerateRequest, background_tasks: BackgroundTasks):
    """
    Regenerate a failed video with optional new prompt
    Useful for fixing policy violations or other non-retryable errors
    """
    try:
        video = await db_service.get_video(video_id)
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")
        
        # Only allow regeneration for failed videos or completed videos user wants to remake
        if video.status not in [VideoStatus.FAILED, VideoStatus.COMPLETED]:
            raise HTTPException(
                status_code=400, 
                detail="Can only regenerate failed or completed videos"
            )
        
        # Get the job to check if it's still active
        job = await db_service.get_job(video.job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Update prompt if provided
        if request.new_prompt:
            await db_service.update_video(video_id, {
                'prompt_text': request.new_prompt,
                'status': VideoStatus.QUEUED,
                'error_message': None,
                'error_type': None,
                'retry_count': 0
            })
        else:
            # Reset video status for retry with same prompt
            await db_service.update_video(video_id, {
                'status': VideoStatus.QUEUED,
                'error_message': None,
                'error_type': None,
                'retry_count': 0
            })
        
        # Import here to avoid circular import
        from services.google_flow_service import google_flow_service
        
        # Start regeneration in background
        background_tasks.add_task(
            google_flow_service.regenerate_single_video,
            video_id
        )
        
        logger.info(f"Started regeneration for video {video_id}")
        
        return {
            "started": True,
            "video_id": video_id,
            "message": "Video regeneration started",
            "new_prompt": request.new_prompt if request.new_prompt else "Using original prompt"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start regeneration: {e}")
        raise HTTPException(status_code=500, detail=str(e))

        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create download: {e}")
        raise HTTPException(status_code=500, detail=str(e))