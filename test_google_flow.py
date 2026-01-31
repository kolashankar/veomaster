#!/usr/bin/env python3
"""
Test script to manually invoke Google Flow service and see errors
"""
import asyncio
import sys
sys.path.insert(0, '/app/backend')

from services.google_flow_service import google_flow_service
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

async def test_google_flow():
    """Test the Google Flow service"""
    try:
        logger.info("Testing Google Flow Service...")
        
        # Test with the job we created
        job_id = "5a0fce14-53e6-489f-92f6-126ff0a2eacf"
        
        logger.info(f"Starting video generation for job {job_id}")
        result = await google_flow_service.generate_videos_for_job(job_id)
        
        logger.info(f"Result: {result}")
        
    except Exception as e:
        logger.error(f"Error occurred: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(test_google_flow())
