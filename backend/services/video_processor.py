import re
import logging
from pathlib import Path
from typing import List, Dict, Tuple
import zipfile
import uuid
from models.video import Video, VideoStatus
from services.database_service import db_service

logger = logging.getLogger(__name__)


class VideoProcessor:
    """
    Service to parse uploaded folders and prompts,
    create video records, and orchestrate generation
    """
    
    def parse_prompts_file(self, file_path: Path) -> Dict[int, str]:
        """
        Parse prompts file format:
        prompt_1: Animate the character...
        prompt_2: ...
        
        Returns: {1: "prompt text", 2: "prompt text", ...}
        """
        prompts = {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Match pattern: prompt_N: text
            pattern = r'prompt_(\d+)\s*:\s*(.+?)(?=\nprompt_\d+|$)'
            matches = re.findall(pattern, content, re.DOTALL | re.MULTILINE)
            
            for match in matches:
                prompt_num = int(match[0])
                prompt_text = match[1].strip()
                prompts[prompt_num] = prompt_text
            
            logger.info(f"Parsed {len(prompts)} prompts from file")
            return prompts
            
        except Exception as e:
            logger.error(f"Failed to parse prompts file: {e}")
            raise
    
    def extract_images_from_folder(self, folder_path: Path) -> Dict[int, Path]:
        """
        Extract images from folder (1.jpeg, 2.jpeg, ...)
        
        Returns: {1: Path, 2: Path, ...}
        """
        images = {}
        
        try:
            # Support common image formats
            image_extensions = ['.jpg', '.jpeg', '.png', '.webp']
            
            for file in folder_path.iterdir():
                if file.suffix.lower() in image_extensions:
                    # Extract number from filename (1.jpeg -> 1)
                    match = re.match(r'(\d+)', file.stem)
                    if match:
                        img_num = int(match.group(1))
                        images[img_num] = file
            
            logger.info(f"Found {len(images)} images in folder")
            return images
            
        except Exception as e:
            logger.error(f"Failed to extract images: {e}")
            raise
    
    def extract_zip(self, zip_path: Path, extract_to: Path) -> Path:
        """
        Extract uploaded zip file to directory
        Returns path to extracted folder
        """
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_to)
            
            # Find the main folder (handle nested zips)
            extracted_items = list(extract_to.iterdir())
            if len(extracted_items) == 1 and extracted_items[0].is_dir():
                return extracted_items[0]
            return extract_to
            
        except Exception as e:
            logger.error(f"Failed to extract zip: {e}")
            raise
    
    def validate_inputs(self, images: Dict[int, Path], prompts: Dict[int, str]) -> Tuple[bool, str]:
        """
        Validate that images and prompts match
        Returns: (is_valid, error_message)
        """
        # Check if counts match
        if len(images) != len(prompts):
            return False, f"Image count ({len(images)}) doesn't match prompt count ({len(prompts)})"
        
        # Check if numbers match
        image_nums = set(images.keys())
        prompt_nums = set(prompts.keys())
        
        if image_nums != prompt_nums:
            missing_images = prompt_nums - image_nums
            missing_prompts = image_nums - prompt_nums
            
            msg = "Mismatch: "
            if missing_images:
                msg += f"Missing images for prompts: {sorted(missing_images)}. "
            if missing_prompts:
                msg += f"Missing prompts for images: {sorted(missing_prompts)}."
            
            return False, msg
        
        return True, ""
    
    async def create_video_records(self, job_id: str, images: Dict[int, Path], prompts: Dict[int, str]) -> List[Video]:
        """
        Create video records in database for each image-prompt pair
        Each pair generates 2 videos (outputs_per_prompt = 2)
        """
        videos = []
        
        for num in sorted(images.keys()):
            image_path = images[num]
            prompt_text = prompts[num]
            
            # Create 2 video records (video_index 1 and 2)
            for video_idx in [1, 2]:
                video_id = str(uuid.uuid4())
                video = Video(
                    id=video_id,
                    job_id=job_id,
                    image_filename=image_path.name,
                    prompt_number=num,
                    prompt_text=prompt_text,
                    video_index=video_idx,
                    status=VideoStatus.QUEUED
                )
                
                await db_service.create_video(video)
                videos.append(video)
        
        logger.info(f"Created {len(videos)} video records for job {job_id}")
        return videos


# Singleton instance
video_processor = VideoProcessor()