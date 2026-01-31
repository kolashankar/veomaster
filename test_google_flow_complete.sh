#!/bin/bash

echo "===================================================================="
echo "Testing Complete Google Flow Video Generation Workflow"
echo "===================================================================="
echo ""

BACKEND_URL="http://localhost:8001/api"
JOB_NAME="Test Upload VP Article $(date +%s)"

echo "Step 1: Create Job"
echo "-------------------"
JOB_RESPONSE=$(curl -s -X POST "$BACKEND_URL/jobs/create" \
  -H "Content-Type: application/json" \
  -d "{\"job_name\": \"$JOB_NAME\"}")

echo "Response: $JOB_RESPONSE"
JOB_ID=$(echo $JOB_RESPONSE | jq -r '.job_id')
echo "Job ID: $JOB_ID"
echo ""

if [ "$JOB_ID" = "null" ] || [ -z "$JOB_ID" ]; then
  echo "❌ Failed to create job"
  exit 1
fi

echo "Step 2: Upload Files (2 images + 2 prompts)"
echo "--------------------------------------------"
UPLOAD_RESPONSE=$(curl -s -X POST "$BACKEND_URL/jobs/$JOB_ID/upload" \
  -F "images_folder=@/app/folder1.zip" \
  -F "prompts_file=@/app/prompts_test_2.txt")

echo "Response: $UPLOAD_RESPONSE"
echo ""

# Check if upload was successful
UPLOADED=$(echo $UPLOAD_RESPONSE | jq -r '.uploaded')
if [ "$UPLOADED" != "true" ]; then
  echo "❌ Failed to upload files"
  echo "Error: $(echo $UPLOAD_RESPONSE | jq -r '.detail')"
  exit 1
fi

IMAGE_COUNT=$(echo $UPLOAD_RESPONSE | jq -r '.image_count')
EXPECTED_VIDEOS=$(echo $UPLOAD_RESPONSE | jq -r '.expected_videos')
echo "✅ Upload successful!"
echo "   - Images: $IMAGE_COUNT"
echo "   - Expected videos: $EXPECTED_VIDEOS"
echo ""

echo "Step 3: Start Video Generation Automation"
echo "------------------------------------------"
START_RESPONSE=$(curl -s -X POST "$BACKEND_URL/jobs/$JOB_ID/start")
echo "Response: $START_RESPONSE"
echo ""

STARTED=$(echo $START_RESPONSE | jq -r '.started')
if [ "$STARTED" = "true" ]; then
  echo "✅ Automation started successfully!"
  echo ""
else
  echo "⚠️  Automation may not have started"
  echo "Message: $(echo $START_RESPONSE | jq -r '.message')"
  echo ""
fi

echo "Step 4: Monitor Job Status"
echo "--------------------------"
echo "Checking job status for 30 seconds..."
echo ""

for i in {1..6}; do
  sleep 5
  JOB_STATUS=$(curl -s "$BACKEND_URL/jobs/$JOB_ID")
  STATUS=$(echo $JOB_STATUS | jq -r '.status')
  PROGRESS=$(echo $JOB_STATUS | jq -r '.progress')
  COMPLETED=$(echo $JOB_STATUS | jq -r '.completed_videos')
  FAILED=$(echo $JOB_STATUS | jq -r '.failed_videos')
  
  echo "[${i}/6] Status: $STATUS | Progress: $PROGRESS | Completed: $COMPLETED | Failed: $FAILED"
done

echo ""
echo "Step 5: Check Video Records"
echo "---------------------------"
VIDEOS=$(curl -s "$BACKEND_URL/videos/job/$JOB_ID")
VIDEO_COUNT=$(echo $VIDEOS | jq '. | length')
echo "Total video records: $VIDEO_COUNT"
echo ""

# Show status of each video
echo "Video statuses:"
echo $VIDEOS | jq -r '.[] | "\(.video_id): \(.status) - \(.prompt_text[:50])..."'

echo ""
echo "===================================================================="
echo "Test Complete! Check Google Flow dashboard at:"
echo "https://labs.google/fx/tools/flow"
echo ""
echo "Job ID: $JOB_ID"
echo "Expected: 4 videos (2 outputs per image)"
echo "===================================================================="
