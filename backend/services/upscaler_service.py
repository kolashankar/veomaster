import asyncio
import logging
import subprocess
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime, timezone
import os

from models.video import Video
from services.database_service import db_service
from services.storage_service import StorageService
from config import TEMP_DOWNLOAD_DIR

logger = logging.getLogger(__name__)


class UpscalerService:
    """
    Service for upscaling videos to 4K using FFmpeg with Lanczos scaling
    """
    
    # Quality presets for FFmpeg
    QUALITY_PRESETS = {
        'fast': {
            'crf': '23',
            'preset': 'fast',
            'description': 'Fast processing, good quality'
        },
        'balanced': {
            'crf': '20',
            'preset': 'medium',
            'description': 'Balanced speed and quality'
        },
        'high': {
            'crf': '18',
            'preset': 'slow',
            'description': 'Highest quality, slower processing'
        }
    }
    
    def __init__(self):
        self.storage_service = StorageService()
        self.upscale_dir = TEMP_DOWNLOAD_DIR / "upscaled"
        self.upscale_dir.mkdir(exist_ok=True)
        logger.info("UpscalerService initialized")
    
    def check_ffmpeg_installed(self) -> bool:
        """
        Check if FFmpeg is installed and available
        """
        try:
            result = subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                logger.info("✅ FFmpeg is installed and available")
                return True
            return False
        except Exception as e:
            logger.error(f"FFmpeg not found: {e}")
            return False
    
    async def upscale_video(
        self,
        input_path: Path,
        output_path: Path,
        quality_preset: str = 'balanced',
        progress_callback=None
    ) -> bool:
        """
        Upscale a single video to 4K resolution
        
        Args:
            input_path: Path to 720p input video
            output_path: Path for 4K output video
            quality_preset: 'fast', 'balanced', or 'high'
            progress_callback: Optional async callback function for progress updates
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.check_ffmpeg_installed():
                logger.error("FFmpeg is not installed")
                return False
            
            if quality_preset not in self.QUALITY_PRESETS:
                logger.warning(f"Invalid preset '{quality_preset}', using 'balanced'")
                quality_preset = 'balanced'
            
            preset = self.QUALITY_PRESETS[quality_preset]
            logger.info(f"Upscaling {input_path.name} with '{quality_preset}' preset...")
            
            # FFmpeg command for 4K upscaling
            # Target: 3840x2160 (4K) with Lanczos filter for best quality
            # Maintain aspect ratio, preserve audio
            cmd = [
                'ffmpeg',
                '-i', str(input_path),
                '-vf', 'scale=3840:2160:flags=lanczos',  # Lanczos scaling to 4K
                '-c:v', 'libx264',  # H.264 codec
                '-preset', preset['preset'],  # Encoding speed preset
                '-crf', preset['crf'],  # Quality (lower = better)
                '-c:a', 'aac',  # Audio codec
                '-b:a', '192k',  # Audio bitrate
                '-movflags', '+faststart',  # Enable streaming
                '-y',  # Overwrite output file
                str(output_path)
            ]
            
            # Run FFmpeg
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Monitor progress
            while True:
                line = await process.stderr.readline()
                if not line:
                    break
                
                line_str = line.decode('utf-8', errors='ignore')
                
                # Parse progress from FFmpeg output
                if 'time=' in line_str and progress_callback:
                    # Extract time information for progress
                    # This is a simplified progress tracking
                    await progress_callback(line_str)
            
            # Wait for completion
            await process.wait()
            
            if process.returncode == 0:
                # Check if output file was created
                if output_path.exists() and output_path.stat().st_size > 0:
                    logger.info(f"✅ Successfully upscaled to {output_path}")
                    return True
                else:
                    logger.error("Output file not created or is empty")
                    return False
            else:
                stderr = await process.stderr.read()
                logger.error(f"FFmpeg failed: {stderr.decode('utf-8', errors='ignore')}")
                return False
                
        except Exception as e:
            logger.error(f"Error upscaling video: {e}")
            return False
    
    async def upscale_videos_batch(
        self,
        video_ids: List[str],
        quality_preset: str = 'balanced',
        task_id: Optional[str] = None
    ) -> Dict[str, bool]:
        """
        Upscale multiple videos in batch with optional progress tracking
        
        Args:
            video_ids: List of video IDs to upscale
            quality_preset: Quality preset to use
            task_id: Optional task ID for progress tracking
        
        Returns:
            Dict mapping video_id to success status
        """
        from services.task_manager import task_manager
        from models.upscale_task import UpscaleTaskStatus
        
        results = {}
        
        logger.info(f"Starting batch upscale of {len(video_ids)} videos with '{quality_preset}' preset")
        
        # Update task status to processing
        if task_id:
            task_manager.update_task_status(task_id, UpscaleTaskStatus.PROCESSING)
            task_manager.add_task_log(
                task_id,
                f"Starting upscaling {len(video_ids)} videos with {quality_preset} quality",
                "info"
            )
        
        for idx, video_id in enumerate(video_ids):
            try:
                # Update progress
                if task_id:
                    progress = (idx / len(video_ids)) * 100
                    task_manager.update_task_progress(task_id, progress, idx, video_id)
                    task_manager.add_task_log(
                        task_id,
                        f"Processing video {idx + 1}/{len(video_ids)}: {video_id}",
                        "info"
                    )
                
                # Get video from database
                video = await db_service.get_video(video_id)
                if not video:
                    logger.error(f"Video {video_id} not found")
                    if task_id:
                        task_manager.add_task_log(task_id, f"Video {video_id} not found", "error")
                        task_manager.increment_failed(task_id)
                    results[video_id] = False
                    continue
                
                # Check if already upscaled
                if video.upscaled:
                    logger.info(f"Video {video_id} already upscaled")
                    if task_id:
                        task_manager.add_task_log(task_id, f"Video already upscaled, skipping", "info")
                        task_manager.increment_completed(task_id)
                    results[video_id] = True
                    continue
                
                # Get 720p video
                input_path = Path(video.local_path_720p) if video.local_path_720p else None
                
                # If not available locally, download from Telegram
                if not input_path or not input_path.exists():
                    logger.info(f"Downloading video {video_id} from Telegram...")
                    if task_id:
                        task_manager.add_task_log(task_id, f"Downloading 720p video from storage...", "info")
                    
                    input_path = TEMP_DOWNLOAD_DIR / f"{video_id}_720p.mp4"
                    
                    if video.telegram_file_id:
                        success = await self.storage_service.download_from_telegram(
                            video.telegram_file_id,
                            input_path
                        )
                        if not success:
                            logger.error(f"Failed to download video {video_id}")
                            if task_id:
                                task_manager.add_task_log(task_id, f"Failed to download video", "error")
                                task_manager.increment_failed(task_id)
                            results[video_id] = False
                            continue
                    else:
                        logger.error(f"No Telegram file_id for video {video_id}")
                        if task_id:
                            task_manager.add_task_log(task_id, f"No storage URL found for video", "error")
                            task_manager.increment_failed(task_id)
                        results[video_id] = False
                        continue
                
                # Prepare output path
                output_filename = f"{video_id}_4k.mp4"
                output_path = self.upscale_dir / output_filename
                
                # Upscale
                logger.info(f"Upscaling video {video_id}...")
                if task_id:
                    task_manager.add_task_log(task_id, f"Applying Lanczos filter and upscaling to 4K...", "info")
                
                success = await self.upscale_video(input_path, output_path, quality_preset)
                
                if success:
                    # Upload 4K version to storage
                    logger.info(f"Uploading 4K video {video_id} to storage...")
                    if task_id:
                        task_manager.add_task_log(task_id, f"Uploading 4K video to storage...", "info")
                    
                    # Upload to R2
                    r2_url = await self.storage_service.upload_to_r2(output_path, output_filename)
                    
                    # Upload to Telegram for permanent storage
                    telegram_data = await self.storage_service.upload_to_telegram(output_path)
                    
                    # Update video record
                    await db_service.update_video(video_id, {
                        'upscaled': True,
                        'upscaled_4k_url': r2_url,
                        'upscaled_telegram_id': telegram_data['file_id'] if telegram_data else None,
                        'upscale_completed_at': datetime.now(timezone.utc),
                        'resolution': '4K'
                    })
                    
                    logger.info(f"✅ Video {video_id} upscaled successfully")
                    if task_id:
                        task_manager.add_task_log(task_id, f"✅ Video upscaled successfully", "success")
                        task_manager.increment_completed(task_id)
                    results[video_id] = True
                else:
                    logger.error(f"Failed to upscale video {video_id}")
                    if task_id:
                        task_manager.add_task_log(task_id, f"FFmpeg upscaling failed", "error")
                        task_manager.increment_failed(task_id)
                    results[video_id] = False
                    
            except Exception as e:
                logger.error(f"Error processing video {video_id}: {e}")
                if task_id:
                    task_manager.add_task_log(task_id, f"Error: {str(e)}", "error")
                    task_manager.increment_failed(task_id)
                results[video_id] = False
        
        successful = sum(1 for v in results.values() if v)
        logger.info(f"Batch upscale complete: {successful}/{len(video_ids)} successful")
        
        # Mark task as complete
        if task_id:
            if successful == len(video_ids):
                task_manager.update_task_status(task_id, UpscaleTaskStatus.COMPLETED)
                task_manager.add_task_log(
                    task_id,
                    f"🎉 All {successful} videos upscaled successfully!",
                    "success"
                )
            elif successful > 0:
                task_manager.update_task_status(task_id, UpscaleTaskStatus.COMPLETED)
                task_manager.add_task_log(
                    task_id,
                    f"Completed with {successful}/{len(video_ids)} successful",
                    "warning"
                )
            else:
                task_manager.update_task_status(task_id, UpscaleTaskStatus.FAILED)
                task_manager.add_task_log(task_id, "All videos failed to upscale", "error")
            
            task_manager.update_task_progress(task_id, 100, len(video_ids))
        
        return results
    
    async def get_video_info(self, video_path: Path) -> Optional[Dict]:
        """
        Get video information using FFprobe
        """
        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                str(video_path)
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                import json
                info = json.loads(stdout.decode('utf-8'))
                
                # Extract useful info
                video_stream = next(
                    (s for s in info.get('streams', []) if s['codec_type'] == 'video'),
                    None
                )
                
                if video_stream:
                    return {
                        'width': video_stream.get('width'),
                        'height': video_stream.get('height'),
                        'duration': float(info.get('format', {}).get('duration', 0)),
                        'size_mb': float(info.get('format', {}).get('size', 0)) / (1024 * 1024),
                        'codec': video_stream.get('codec_name')
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting video info: {e}")
            return None
    
    async def estimate_upscale_time(self, video_duration_seconds: float, quality_preset: str) -> float:
        """
        Estimate upscaling time based on video duration and quality preset
        
        Returns estimated time in seconds
        """
        # Rough estimates (actual time varies by hardware)
        # Assuming processing is ~2-5x real-time depending on preset
        multipliers = {
            'fast': 2.0,
            'balanced': 3.5,
            'high': 5.0
        }
        
        multiplier = multipliers.get(quality_preset, 3.5)
        estimated_seconds = video_duration_seconds * multiplier
        
        return estimated_seconds
    
    def cleanup_temp_files(self, video_id: str):
        """
        Clean up temporary files for a video
        """
        try:
            patterns = [
                f"{video_id}_720p.mp4",
                f"{video_id}_4k.mp4"
            ]
            
            for pattern in patterns:
                file_path = TEMP_DOWNLOAD_DIR / pattern
                if file_path.exists():
                    file_path.unlink()
                    logger.info(f"Cleaned up {file_path.name}")
                
                upscale_path = self.upscale_dir / pattern
                if upscale_path.exists():
                    upscale_path.unlink()
                    logger.info(f"Cleaned up {upscale_path.name}")
                    
        except Exception as e:
            logger.error(f"Error cleaning up temp files: {e}")


# Singleton instance
upscaler_service = UpscalerService()
