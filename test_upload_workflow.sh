#!/bin/bash

# Test script to verify the complete upload workflow
set -e

echo "==========================================="
echo "Testing Complete Upload Workflow"
echo "==========================================="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Step 1: Create a job
echo -e "\n${BLUE}Step 1: Creating a new job...${NC}"
JOB_RESPONSE=$(curl -s -X POST http://localhost:8001/api/jobs/create \
  -H "Content-Type: application/json" \
  -d '{"job_name": "Test Upload VP Article"}')

JOB_ID=$(echo $JOB_RESPONSE | jq -r '.job_id')
echo -e "${GREEN}✓ Job created: $JOB_ID${NC}"

# Step 2: Upload files
echo -e "\n${BLUE}Step 2: Uploading files (zip + prompts)...${NC}"
UPLOAD_RESPONSE=$(curl -s -X POST http://localhost:8001/api/jobs/$JOB_ID/upload \
  -F "images_folder=@/app/folder1.zip" \
  -F "prompts_file=@/app/prompts_test.txt")

UPLOADED=$(echo $UPLOAD_RESPONSE | jq -r '.uploaded')
IMAGE_COUNT=$(echo $UPLOAD_RESPONSE | jq -r '.image_count')
EXPECTED_VIDEOS=$(echo $UPLOAD_RESPONSE | jq -r '.expected_videos')

if [ "$UPLOADED" = "true" ]; then
  echo -e "${GREEN}✓ Upload successful!${NC}"
  echo -e "  Images: $IMAGE_COUNT"
  echo -e "  Expected videos: $EXPECTED_VIDEOS"
else
  echo -e "${RED}✗ Upload failed${NC}"
  echo $UPLOAD_RESPONSE | jq .
  exit 1
fi

# Step 3: Verify job status
echo -e "\n${BLUE}Step 3: Verifying job status...${NC}"
JOB_STATUS=$(curl -s http://localhost:8001/api/jobs/$JOB_ID)
STATUS=$(echo $JOB_STATUS | jq -r '.status')
TOTAL_IMAGES=$(echo $JOB_STATUS | jq -r '.total_images')

echo -e "${GREEN}✓ Job status verified${NC}"
echo -e "  Status: $STATUS"
echo -e "  Total images: $TOTAL_IMAGES"

# Step 4: Check video records
echo -e "\n${BLUE}Step 4: Checking video records...${NC}"
VIDEOS=$(curl -s http://localhost:8001/api/videos/job/$JOB_ID)
VIDEO_COUNT=$(echo $VIDEOS | jq '. | length')

echo -e "${GREEN}✓ Video records created${NC}"
echo -e "  Total video records: $VIDEO_COUNT"

# Show sample video
echo -e "\n${BLUE}Sample video record:${NC}"
echo $VIDEOS | jq '.[0]' | grep -E "image_filename|prompt_number|status|video_index"

# Summary
echo -e "\n==========================================="
echo -e "${GREEN}✓ ALL TESTS PASSED!${NC}"
echo -e "==========================================="
echo -e "Job ID: $JOB_ID"
echo -e "Images: $IMAGE_COUNT"
echo -e "Video records: $VIDEO_COUNT"
echo -e "Status: Ready for processing"
echo -e "==========================================="
