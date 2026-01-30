import asyncio
import logging
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from datetime import datetime, timezone
import re

from playwright.async_api import async_playwright, Page, Browser, BrowserContext, TimeoutError as PlaywrightTimeoutError
from models.video import Video, VideoStatus, ErrorType
from models.session import GoogleFlowSession
from services.database_service import db_service
from services.storage_service import StorageService
from config import (
    GOOGLE_FLOW_EMAIL,
    GOOGLE_FLOW_PASSWORD,
    GOOGLE_FLOW_URL,
    VIDEO_OUTPUTS_PER_PROMPT,
    ASPECT_RATIO,
    MODEL_NAME,
    DOWNLOAD_QUALITY,
    HIGH_DEMAND_RETRY_DELAY_SECONDS,
    MAX_RETRY_ATTEMPTS,
    GENERATION_POLL_INTERVAL_SECONDS,
    TEMP_DOWNLOAD_DIR
)

logger = logging.getLogger(__name__)


class GoogleFlowService:
    """
    Core automation service for Google Flow video generation
    Handles browser automation, session management, and video generation workflow
    """
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.storage_service = StorageService()
        self.session_id: Optional[str] = None
        logger.info("GoogleFlowService initialized")
    
    # =============== BROWSER MANAGEMENT ===============
    
    async def initialize_browser(self) -> bool:
        """
        Initialize Playwright browser with proper configuration
        """
        try:
            logger.info("Initializing Playwright browser...")
            playwright = await async_playwright().start()
            
            self.browser = await playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu'
                ]
            )
            
            # Check for existing session
            session = await db_service.get_active_session()
            
            if session and session.session_active:
                logger.info("Found active session, attempting to restore...")
                self.context = await self.browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent=session.user_agent
                )
                await self.context.add_cookies(session.cookies)
                self.session_id = session.id
            else:
                logger.info("Creating new browser context...")
                self.context = await self.browser.new_context(
                    viewport={'width': 1920, 'height': 1080}
                )
            
            self.page = await self.context.new_page()
            logger.info("✅ Browser initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize browser: {e}")
            return False
    
    async def close_browser(self):
        """Clean up browser resources"""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            logger.info("Browser closed successfully")
        except Exception as e:
            logger.error(f"Error closing browser: {e}")
    
    # =============== SESSION & LOGIN MANAGEMENT ===============
    
    async def check_and_login(self) -> bool:
        """
        Check if logged in to Google Flow, perform login if needed
        Returns True if login successful or already logged in
        """
        try:
            logger.info("Checking login status...")
            await self.page.goto(GOOGLE_FLOW_URL, wait_until='networkidle', timeout=30000)
            
            # Wait a bit for page to load
            await asyncio.sleep(3)
            
            # Check if already logged in (look for user profile or Flow UI elements)
            # Google Flow might show "Sign in" button if not logged in
            is_logged_in = await self._check_logged_in_state()
            
            if is_logged_in:
                logger.info("✅ Already logged in to Google Flow")
                await self._save_session()
                return True
            
            # Need to login
            logger.info("Not logged in, attempting login...")
            return await self._perform_login()
            
        except Exception as e:
            logger.error(f"Login check failed: {e}")
            return False
    
    async def _check_logged_in_state(self) -> bool:
        """
        Check if user is currently logged in to Google Flow
        """
        try:
            # Look for signs of being logged in
            # This might need adjustment based on actual Google Flow UI
            
            # Method 1: Check for "Sign in" button (if present, not logged in)
            sign_in_button = await self.page.query_selector('text="Sign in"')
            if sign_in_button:
                return False
            
            # Method 2: Check for Flow interface elements
            # Look for "New project" or similar buttons
            new_project_btn = await self.page.query_selector('text="New project"')
            if new_project_btn:
                return True
            
            # Method 3: Check URL or page title
            current_url = self.page.url
            if 'accounts.google.com' in current_url:
                return False
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking login state: {e}")
            return False
    
    async def _perform_login(self) -> bool:
        """
        Perform Google account login
        """
        try:
            logger.info("Starting login process...")
            
            # Click Sign In button
            sign_in_selector = 'text="Sign in"'
            await self.page.click(sign_in_selector, timeout=10000)
            await asyncio.sleep(2)
            
            # Enter email
            logger.info("Entering email...")
            email_input = await self.page.wait_for_selector('input[type="email"]', timeout=10000)
            await email_input.fill(GOOGLE_FLOW_EMAIL)
            await asyncio.sleep(1)
            
            # Click Next
            await self.page.click('button:has-text("Next")', timeout=5000)
            await asyncio.sleep(3)
            
            # Enter password
            logger.info("Entering password...")
            password_input = await self.page.wait_for_selector('input[type="password"]', timeout=10000)
            await password_input.fill(GOOGLE_FLOW_PASSWORD)
            await asyncio.sleep(1)
            
            # Click Next
            await self.page.click('button:has-text("Next")', timeout=5000)
            await asyncio.sleep(5)
            
            # Wait for navigation back to Flow
            await self.page.wait_for_url(f'**/flow**', timeout=20000)
            
            logger.info("✅ Login successful")
            await self._save_session()
            return True
            
        except PlaywrightTimeoutError as e:
            logger.error(f"Login timeout: {e}")
            # Take screenshot for debugging
            await self.page.screenshot(path=str(TEMP_DOWNLOAD_DIR / "login_error.png"))
            return False
        except Exception as e:
            logger.error(f"Login failed: {e}")
            return False
    
    async def _save_session(self):
        """Save current session cookies to database"""
        try:
            cookies = await self.context.cookies()
            user_agent = await self.page.evaluate('() => navigator.userAgent')
            
            # Create or update session
            if self.session_id:
                await db_service.update_session(self.session_id, {
                    'cookies': cookies,
                    'user_agent': user_agent,
                    'session_active': True,
                    'last_used_at': datetime.now(timezone.utc)
                })
            else:
                session = GoogleFlowSession(
                    session_active=True,
                    cookies=cookies,
                    user_agent=user_agent,
                    login_email=GOOGLE_FLOW_EMAIL,
                    last_login_at=datetime.now(timezone.utc),
                    last_used_at=datetime.now(timezone.utc)
                )
                saved_session = await db_service.save_session(session)
                self.session_id = saved_session.id
            
            logger.info("Session saved successfully")
            
        except Exception as e:
            logger.error(f"Failed to save session: {e}")
    
    # =============== PROJECT CREATION & CONFIGURATION ===============
    
    async def create_new_project(self) -> bool:
        """
        Create a new Flow project
        """
        try:
            logger.info("Creating new project...")
            
            # Click "New project" button
            new_project_btn = await self.page.wait_for_selector('text="New project"', timeout=10000)
            await new_project_btn.click()
            await asyncio.sleep(3)
            
            # Look for "Frames to Video" or similar option
            # This selector might need adjustment based on actual UI
            frames_to_video = await self.page.wait_for_selector('text="Frames to Video"', timeout=10000)
            await frames_to_video.click()
            await asyncio.sleep(2)
            
            logger.info("✅ Project created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create project: {e}")
            return False
    
    async def set_portrait_mode(self) -> bool:
        """
        Set aspect ratio to portrait
        """
        try:
            logger.info("Setting aspect ratio to portrait...")
            
            # Find aspect ratio dropdown
            # This might be a select element or custom dropdown
            aspect_dropdown = await self.page.wait_for_selector('[aria-label*="aspect ratio"], [aria-label*="Aspect ratio"]', timeout=10000)
            await aspect_dropdown.click()
            await asyncio.sleep(1)
            
            # Select Portrait option
            portrait_option = await self.page.wait_for_selector('text="Portrait"', timeout=5000)
            await portrait_option.click()
            await asyncio.sleep(1)
            
            logger.info("✅ Aspect ratio set to portrait")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set portrait mode: {e}")
            return False
    
    async def set_outputs_and_model(self) -> bool:
        """
        Set outputs per prompt to 2 and select Veo 3.1 Fast model
        """
        try:
            logger.info("Configuring outputs and model...")
            
            # Set outputs per prompt to 2
            outputs_input = await self.page.wait_for_selector('[aria-label*="outputs"], [placeholder*="outputs"]', timeout=10000)
            await outputs_input.fill(str(VIDEO_OUTPUTS_PER_PROMPT))
            await asyncio.sleep(1)
            
            # Select model: Veo 3.1 - Fast [Lower Priority]
            model_dropdown = await self.page.wait_for_selector('[aria-label*="model"], [aria-label*="Model"]', timeout=10000)
            await model_dropdown.click()
            await asyncio.sleep(1)
            
            # Select the specific model
            model_option = await self.page.wait_for_selector(f'text="{MODEL_NAME}"', timeout=5000)
            await model_option.click()
            await asyncio.sleep(1)
            
            logger.info(f"✅ Set {VIDEO_OUTPUTS_PER_PROMPT} outputs per prompt with {MODEL_NAME}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to configure outputs/model: {e}")
            return False
    
    # =============== VIDEO GENERATION ===============
    
    async def upload_reference_and_prompt(self, image_path: Path, prompt_text: str) -> bool:
        """
        Upload reference image and enter prompt text
        """
        try:
            logger.info(f"Uploading image and prompt for: {image_path.name}")
            
            # Upload image
            upload_button = await self.page.wait_for_selector('input[type="file"], [aria-label*="upload image"]', timeout=10000)
            await upload_button.set_input_files(str(image_path))
            await asyncio.sleep(2)
            
            # Enter prompt text
            prompt_textarea = await self.page.wait_for_selector('textarea[placeholder*="prompt"], textarea[aria-label*="prompt"]', timeout=10000)
            await prompt_textarea.fill(prompt_text)
            await asyncio.sleep(1)
            
            logger.info("✅ Image and prompt uploaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to upload image/prompt: {e}")
            return False
    
    async def start_generation(self) -> bool:
        """
        Click the Generate button to start video generation
        """
        try:
            logger.info("Starting video generation...")
            
            generate_button = await self.page.wait_for_selector('button:has-text("Generate")', timeout=10000)
            await generate_button.click()
            await asyncio.sleep(2)
            
            logger.info("✅ Generation started")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start generation: {e}")
            return False
    
    async def wait_for_generation(self, video: Video, max_wait_minutes: int = 30) -> Tuple[bool, Optional[ErrorType], Optional[str]]:
        """
        Monitor generation status until complete or error
        
        Returns:
            (success, error_type, error_message)
        """
        try:
            logger.info(f"Monitoring generation for video {video.id}...")
            
            start_time = datetime.now(timezone.utc)
            max_wait_seconds = max_wait_minutes * 60
            
            while True:
                # Check timeout
                elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
                if elapsed > max_wait_seconds:
                    return False, ErrorType.TIMEOUT, f"Generation timeout after {max_wait_minutes} minutes"
                
                # Check page for status
                status_info = await self._check_generation_status()
                
                if status_info['completed']:
                    logger.info("✅ Generation completed successfully")
                    return True, None, None
                
                if status_info['error']:
                    error_type, error_msg = await self._categorize_error(status_info['error_message'])
                    logger.warning(f"Generation error: {error_msg} (Type: {error_type})")
                    return False, error_type, error_msg
                
                # Still generating, wait and check again
                await asyncio.sleep(GENERATION_POLL_INTERVAL_SECONDS)
                
        except Exception as e:
            logger.error(f"Error while waiting for generation: {e}")
            return False, ErrorType.UNKNOWN, str(e)
    
    async def _check_generation_status(self) -> Dict:
        """
        Check current generation status on the page
        
        Returns dict with: completed (bool), error (bool), error_message (str)
        """
        try:
            # Look for completion indicators
            download_button = await self.page.query_selector('button:has-text("Download")')
            if download_button and await download_button.is_visible():
                return {'completed': True, 'error': False, 'error_message': None}
            
            # Look for error messages
            error_indicators = [
                'text="Flow is experiencing high demand"',
                'text*="policy"',
                'text*="violation"',
                'text*="prominent people"',
                'text*="error"',
                'text*="failed"'
            ]
            
            for indicator in error_indicators:
                error_element = await self.page.query_selector(indicator)
                if error_element and await error_element.is_visible():
                    error_text = await error_element.inner_text()
                    return {'completed': False, 'error': True, 'error_message': error_text}
            
            # Still generating
            return {'completed': False, 'error': False, 'error_message': None}
            
        except Exception as e:
            logger.error(f"Error checking status: {e}")
            return {'completed': False, 'error': True, 'error_message': str(e)}
    
    async def _categorize_error(self, error_message: str) -> Tuple[ErrorType, str]:
        """
        Categorize error as retryable or non-retryable
        
        Returns: (ErrorType, formatted_message)
        """
        error_lower = error_message.lower()
        
        # Retryable: High demand
        if 'high demand' in error_lower or 'busy' in error_lower:
            return ErrorType.HIGH_DEMAND, error_message
        
        # Non-retryable: Policy violations
        if 'prominent people' in error_lower:
            return ErrorType.PROMINENT_PEOPLE, error_message
        
        if 'policy' in error_lower or 'violation' in error_lower:
            return ErrorType.POLICY_VIOLATION, error_message
        
        if 'content' in error_lower and 'filter' in error_lower:
            return ErrorType.CONTENT_FILTER, error_message
        
        # Default to unknown
        return ErrorType.UNKNOWN, error_message
    
    async def handle_error_with_retry(self, video: Video, error_type: ErrorType, error_message: str) -> bool:
        """
        Handle error with appropriate retry logic
        
        Returns True if should retry, False otherwise
        """
        try:
            # Update video with error
            await db_service.update_video(video.id, {
                'error_type': error_type,
                'error_message': error_message,
                'retry_count': video.retry_count + 1
            })
            
            # Check if retryable
            if error_type == ErrorType.HIGH_DEMAND:
                if video.retry_count < MAX_RETRY_ATTEMPTS:
                    logger.info(f"High demand error, waiting {HIGH_DEMAND_RETRY_DELAY_SECONDS}s before retry {video.retry_count + 1}/{MAX_RETRY_ATTEMPTS}")
                    await asyncio.sleep(HIGH_DEMAND_RETRY_DELAY_SECONDS)
                    return True
                else:
                    logger.warning(f"Max retry attempts reached for video {video.id}")
                    await db_service.update_video(video.id, {'status': VideoStatus.FAILED})
                    return False
            
            # Non-retryable errors
            logger.warning(f"Non-retryable error for video {video.id}: {error_type}")
            await db_service.update_video(video.id, {'status': VideoStatus.FAILED})
            return False
            
        except Exception as e:
            logger.error(f"Error handling retry logic: {e}")
            return False
    
    # =============== VIDEO DOWNLOAD ===============
    
    async def download_video_720p(self, video: Video, output_path: Path) -> bool:
        """
        Download generated video in 720p quality
        """
        try:
            logger.info(f"Downloading video {video.id} in 720p...")
            
            # Click download button
            download_button = await self.page.wait_for_selector('button:has-text("Download")', timeout=10000)
            await download_button.click()
            await asyncio.sleep(2)
            
            # Select 720p quality option
            quality_option = await self.page.wait_for_selector(f'text="{DOWNLOAD_QUALITY}"', timeout=5000)
            await quality_option.click()
            
            # Wait for download to complete
            async with self.page.expect_download() as download_info:
                download = await download_info.value
                await download.save_as(str(output_path))
            
            logger.info(f"✅ Video downloaded successfully to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to download video: {e}")
            return False
    
    # =============== MAIN WORKFLOW ===============
    
    async def generate_videos_for_job(self, job_id: str) -> bool:
        """
        Main workflow to generate all videos for a job
        """
        try:
            logger.info(f"Starting video generation workflow for job {job_id}")
            
            # Initialize browser
            if not await self.initialize_browser():
                return False
            
            # Login
            if not await self.check_and_login():
                await self.close_browser()
                return False
            
            # Get job and videos
            job = await db_service.get_job(job_id)
            if not job:
                logger.error(f"Job {job_id} not found")
                return False
            
            videos = await db_service.get_videos_by_job(job_id)
            
            # Update job status
            await db_service.update_job(job_id, {'status': 'processing'})
            
            # Process each image-prompt pair
            processed_images = set()
            
            for video in videos:
                # Skip if already processed this image-prompt pair
                image_key = f"{video.prompt_number}_{video.video_index}"
                if image_key in processed_images:
                    continue
                
                logger.info(f"Processing video {video.id} - Image {video.prompt_number}, Output {video.video_index}")
                
                # Update video status
                await db_service.update_video(video.id, {
                    'status': VideoStatus.GENERATING,
                    'generation_started_at': datetime.now(timezone.utc)
                })
                
                # Create new project
                if not await self.create_new_project():
                    continue
                
                # Configure project
                await self.set_portrait_mode()
                await self.set_outputs_and_model()
                
                # Get image path
                image_path = Path(job.images_folder_path) / video.image_filename
                
                # Upload and generate
                if not await self.upload_reference_and_prompt(image_path, video.prompt_text):
                    await db_service.update_video(video.id, {
                        'status': VideoStatus.FAILED,
                        'error_message': 'Failed to upload image/prompt'
                    })
                    continue
                
                if not await self.start_generation():
                    await db_service.update_video(video.id, {
                        'status': VideoStatus.FAILED,
                        'error_message': 'Failed to start generation'
                    })
                    continue
                
                # Wait for completion with retry logic
                retry_count = 0
                while retry_count <= MAX_RETRY_ATTEMPTS:
                    success, error_type, error_msg = await self.wait_for_generation(video)
                    
                    if success:
                        # Download video
                        output_filename = f"{job_id}_{video.prompt_number}_{video.video_index}.mp4"
                        output_path = TEMP_DOWNLOAD_DIR / output_filename
                        
                        if await self.download_video_720p(video, output_path):
                            # Upload to storage
                            r2_url = await self.storage_service.upload_to_r2(output_path, output_filename)
                            telegram_data = await self.storage_service.upload_to_telegram(output_path)
                            
                            # Update video record
                            await db_service.update_video(video.id, {
                                'status': VideoStatus.COMPLETED,
                                'generation_completed_at': datetime.now(timezone.utc),
                                'cloudflare_url': r2_url,
                                'telegram_file_id': telegram_data['file_id'] if telegram_data else None,
                                'telegram_url': telegram_data['cdn_url'] if telegram_data else None,
                                'local_path_720p': str(output_path)
                            })
                            
                            # Update job progress
                            completed_count = len(await db_service.get_completed_videos(job_id))
                            await db_service.update_job(job_id, {
                                'completed_videos': completed_count,
                                'current_processing': video.prompt_number
                            })
                        
                        break  # Success, move to next video
                    
                    # Handle error
                    should_retry = await self.handle_error_with_retry(video, error_type, error_msg)
                    if should_retry:
                        retry_count += 1
                        logger.info(f"Retrying video {video.id} (attempt {retry_count})")
                        continue
                    else:
                        # Failed permanently
                        failed_count = len(await db_service.get_failed_videos(job_id))
                        await db_service.update_job(job_id, {'failed_videos': failed_count})
                        break
                
                processed_images.add(image_key)
            
            # Mark job as completed
            await db_service.update_job(job_id, {'status': 'completed'})
            logger.info(f"✅ Job {job_id} completed")
            
            await self.close_browser()
            return True
            
        except Exception as e:
            logger.error(f"Error in video generation workflow: {e}")
            await db_service.update_job(job_id, {
                'status': 'failed',
                'error_summary': [str(e)]
            })
            await self.close_browser()
            return False

    
    async def regenerate_single_video(self, video_id: str) -> bool:
        """
        Regenerate a single failed video
        Used when user wants to retry a specific video with or without a new prompt
        """
        try:
            logger.info(f"Starting regeneration for video {video_id}")
            
            # Get video details
            video = await db_service.get_video(video_id)
            if not video:
                logger.error(f"Video {video_id} not found")
                return False
            
            # Get job details
            job = await db_service.get_job(video.job_id)
            if not job:
                logger.error(f"Job {video.job_id} not found")
                return False
            
            # Initialize browser if not already
            if not self.browser:
                if not await self.initialize_browser():
                    logger.error("Failed to initialize browser")
                    return False
            
            # Check/login
            if not await self.check_and_login():
                logger.error("Failed to login to Google Flow")
                return False
            
            # Update video status
            await db_service.update_video(video_id, {
                'status': VideoStatus.GENERATING,
                'generation_started_at': datetime.now(timezone.utc)
            })
            
            # Create new project
            if not await self.create_new_project():
                await db_service.update_video(video_id, {
                    'status': VideoStatus.FAILED,
                    'error_message': 'Failed to create new project'
                })
                return False
            
            # Configure project
            await self.set_portrait_mode()
            await self.set_outputs_and_model()
            
            # Get image path
            image_path = Path(job.images_folder_path) / video.image_filename
            
            # Upload and generate
            if not await self.upload_reference_and_prompt(image_path, video.prompt_text):
                await db_service.update_video(video_id, {
                    'status': VideoStatus.FAILED,
                    'error_message': 'Failed to upload image/prompt'
                })
                return False
            
            if not await self.start_generation():
                await db_service.update_video(video_id, {
                    'status': VideoStatus.FAILED,
                    'error_message': 'Failed to start generation'
                })
                return False
            
            # Wait for completion with retry logic
            retry_count = 0
            while retry_count <= MAX_RETRY_ATTEMPTS:
                success, error_type, error_msg = await self.wait_for_generation(video)
                
                if success:
                    # Download video
                    output_filename = f"{video.job_id}_{video.prompt_number}_{video.video_index}_regen.mp4"
                    output_path = TEMP_DOWNLOAD_DIR / output_filename
                    
                    if await self.download_video_720p(video, output_path):
                        # Upload to storage
                        r2_url = await self.storage_service.upload_to_r2(output_path, output_filename)
                        telegram_data = await self.storage_service.upload_to_telegram(output_path)
                        
                        # Update video record
                        await db_service.update_video(video_id, {
                            'status': VideoStatus.COMPLETED,
                            'generation_completed_at': datetime.now(timezone.utc),
                            'cloudflare_url': r2_url,
                            'telegram_file_id': telegram_data['file_id'] if telegram_data else None,
                            'telegram_url': telegram_data['cdn_url'] if telegram_data else None,
                            'local_path_720p': str(output_path)
                        })
                        
                        # Update job counters
                        completed_count = len(await db_service.get_completed_videos(video.job_id))
                        failed_count = len(await db_service.get_failed_videos(video.job_id))
                        await db_service.update_job(video.job_id, {
                            'completed_videos': completed_count,
                            'failed_videos': failed_count
                        })
                        
                        logger.info(f"✅ Successfully regenerated video {video_id}")
                        return True
                    
                # Handle error
                should_retry = await self.handle_error_with_retry(video, error_type, error_msg)
                if should_retry:
                    retry_count += 1
                    logger.info(f"Retrying video {video_id} (attempt {retry_count})")
                    continue
                else:
                    # Failed permanently
                    failed_count = len(await db_service.get_failed_videos(video.job_id))
                    await db_service.update_job(video.job_id, {'failed_videos': failed_count})
                    logger.error(f"Failed to regenerate video {video_id}")
                    return False
            
            # Max retries reached
            logger.error(f"Max retries reached for video {video_id}")
            return False
            
        except Exception as e:
            logger.error(f"Error in video regeneration: {e}")
            await db_service.update_video(video_id, {
                'status': VideoStatus.FAILED,
                'error_message': str(e)
            })
            return False



# Singleton instance
google_flow_service = GoogleFlowService()
