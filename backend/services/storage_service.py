import logging
import asyncio
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta, timezone
import aiofiles
import os

logger = logging.getLogger(__name__)


class StorageService:
    """
    Hybrid storage service using Cloudflare R2 + Telegram CDN
    Using mock credentials for development
    """
    
    def __init__(self):
        from config import (
            CLOUDFLARE_ACCOUNT_ID,
            CLOUDFLARE_ACCESS_KEY,
            CLOUDFLARE_SECRET_KEY,
            CLOUDFLARE_BUCKET_NAME,
            TELEGRAM_BOT_TOKEN,
            TELEGRAM_CHANNEL_ID,
            CLOUDFLARE_R2_TTL_HOURS
        )
        
        self.cf_account_id = CLOUDFLARE_ACCOUNT_ID
        self.cf_access_key = CLOUDFLARE_ACCESS_KEY
        self.cf_secret_key = CLOUDFLARE_SECRET_KEY
        self.cf_bucket = CLOUDFLARE_BUCKET_NAME
        self.telegram_token = TELEGRAM_BOT_TOKEN
        self.telegram_channel = TELEGRAM_CHANNEL_ID
        self.r2_ttl_hours = CLOUDFLARE_R2_TTL_HOURS
        
        logger.info("StorageService initialized with mock credentials")
    
    # =============== CLOUDFLARE R2 OPERATIONS ===============
    
    async def upload_to_r2(self, file_path: Path, object_key: str) -> Optional[str]:
        """
        Upload video to Cloudflare R2 (temporary storage)
        Returns public URL
        
        NOTE: Using mock implementation for development
        In production, this would use boto3 with R2 endpoint
        """
        try:
            logger.info(f"[MOCK] Uploading to R2: {object_key}")
            
            # Mock implementation - in production, use boto3:
            # import boto3
            # s3_client = boto3.client(
            #     's3',
            #     endpoint_url=f'https://{self.cf_account_id}.r2.cloudflarestorage.com',
            #     aws_access_key_id=self.cf_access_key,
            #     aws_secret_access_key=self.cf_secret_key
            # )
            # s3_client.upload_file(str(file_path), self.cf_bucket, object_key)
            
            # Generate mock URL
            mock_url = f"https://r2-cdn.example.com/{self.cf_bucket}/{object_key}"
            
            # Schedule deletion after TTL
            asyncio.create_task(self._schedule_r2_deletion(object_key))
            
            logger.info(f"[MOCK] R2 upload successful: {mock_url}")
            return mock_url
            
        except Exception as e:
            logger.error(f"Failed to upload to R2: {e}")
            return None
    
    async def _schedule_r2_deletion(self, object_key: str):
        """Schedule automatic deletion after TTL"""
        await asyncio.sleep(self.r2_ttl_hours * 3600)
        await self.delete_from_r2(object_key)
    
    async def delete_from_r2(self, object_key: str) -> bool:
        """Delete video from R2"""
        try:
            logger.info(f"[MOCK] Deleting from R2: {object_key}")
            # Mock implementation
            # s3_client.delete_object(Bucket=self.cf_bucket, Key=object_key)
            return True
        except Exception as e:
            logger.error(f"Failed to delete from R2: {e}")
            return False
    
    async def get_r2_signed_url(self, object_key: str, expiry_seconds: int = 3600) -> Optional[str]:
        """Generate temporary signed URL for R2 object"""
        try:
            logger.info(f"[MOCK] Generating signed URL for: {object_key}")
            # Mock implementation
            mock_url = f"https://r2-cdn.example.com/{self.cf_bucket}/{object_key}?expires={expiry_seconds}"
            return mock_url
        except Exception as e:
            logger.error(f"Failed to generate signed URL: {e}")
            return None
    
    # =============== TELEGRAM CDN OPERATIONS ===============
    
    async def upload_to_telegram(self, file_path: Path) -> Optional[dict]:
        """
        Upload video to Telegram channel (permanent storage)
        Returns dict with file_id and cdn_url
        
        NOTE: Using mock implementation for development
        In production, this would use python-telegram-bot
        """
        try:
            logger.info(f"[MOCK] Uploading to Telegram: {file_path.name}")
            
            # Mock implementation - in production:
            # from telegram import Bot
            # bot = Bot(token=self.telegram_token)
            # with open(file_path, 'rb') as video_file:
            #     message = await bot.send_video(
            #         chat_id=self.telegram_channel,
            #         video=video_file
            #     )
            # file_id = message.video.file_id
            
            # Generate mock IDs
            mock_file_id = f"mock_tg_file_{file_path.stem}_{datetime.now(timezone.utc).timestamp()}"
            mock_cdn_url = f"https://telegram-cdn.example.com/file/{mock_file_id}"
            
            logger.info(f"[MOCK] Telegram upload successful: {mock_file_id}")
            return {
                "file_id": mock_file_id,
                "cdn_url": mock_cdn_url
            }
            
        except Exception as e:
            logger.error(f"Failed to upload to Telegram: {e}")
            return None
    
    async def download_from_telegram(self, file_id: str, destination: Path) -> bool:
        """
        Download video from Telegram using file_id
        """
        try:
            logger.info(f"[MOCK] Downloading from Telegram: {file_id}")
            
            # Mock implementation - in production:
            # from telegram import Bot
            # bot = Bot(token=self.telegram_token)
            # file = await bot.get_file(file_id)
            # await file.download_to_drive(str(destination))
            
            # For mock, just log
            logger.info(f"[MOCK] Telegram download would save to: {destination}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to download from Telegram: {e}")
            return False
    
    # =============== HYBRID WORKFLOW ===============
    
    async def store_video(self, file_path: Path, job_id: str, video_id: str) -> dict:
        """
        Complete storage workflow:
        1. Upload to R2 (fast, temporary)
        2. Upload to Telegram (slower, permanent) in background
        3. Return URLs
        """
        result = {
            "cloudflare_url": None,
            "telegram_file_id": None,
            "telegram_url": None
        }
        
        # Generate object key
        object_key = f"{job_id}/{video_id}/{file_path.name}"
        
        # Upload to R2 (immediate)
        r2_url = await self.upload_to_r2(file_path, object_key)
        result["cloudflare_url"] = r2_url
        
        # Upload to Telegram (background)
        telegram_data = await self.upload_to_telegram(file_path)
        if telegram_data:
            result["telegram_file_id"] = telegram_data["file_id"]
            result["telegram_url"] = telegram_data["cdn_url"]
        
        return result


# Singleton instance
storage_service = StorageService()