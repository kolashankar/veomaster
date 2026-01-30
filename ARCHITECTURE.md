# Google Flow Video Automation Platform - System Architecture

## 1. System Overview

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Browser                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │          React Frontend (Port 3000)                       │  │
│  │  - Dashboard  - Job Details  - Video Gallery             │  │
│  │  - Upscale Modal  - Download Manager                     │  │
│  └────────────────────┬─────────────────────────────────────┘  │
└────────────────────────┼─────────────────────────────────────────┘
                         │ HTTPS/REST API
                         │
┌────────────────────────▼─────────────────────────────────────────┐
│                   FastAPI Backend (Port 8001)                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    API Routes                             │  │
│  │  /api/jobs  /api/videos  /api/upload  /api/download      │  │
│  └────────────────────┬─────────────────────────────────────┘  │
│                       │                                          │
│  ┌────────────────────┴─────────────────────────────────────┐  │
│  │              Core Services Layer                          │  │
│  │  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐  │  │
│  │  │   Google    │  │    Video     │  │    Storage     │  │  │
│  │  │    Flow     │  │  Processor   │  │    Service     │  │  │
│  │  │   Service   │  │   Service    │  │                │  │  │
│  │  └──────┬──────┘  └──────┬───────┘  └────────┬───────┘  │  │
│  └─────────┼────────────────┼──────────────────┬─┼──────────┘  │
└────────────┼────────────────┼──────────────────┼─┼──────────────┘
             │                │                  │ │
     ┌───────▼────────┐  ┌────▼─────┐  ┌────────▼─▼────────┐
     │   Playwright   │  │  FFmpeg  │  │     MongoDB       │
     │    Browser     │  │  Video   │  │   (Database)      │
     │   Automation   │  │Processing│  └───────────────────┘
     └───────┬────────┘  └──────────┘
             │                              ┌─────────────────┐
     ┌───────▼─────────┐                   │  Cloudflare R2  │
     │  Google Flow    │                   │  (Temp Storage) │
     │  (labs.google)  │                   │   2hr TTL       │
     └─────────────────┘                   └─────────────────┘
                                           
                                           ┌─────────────────┐
                                           │  Telegram CDN   │
                                           │  (Permanent)    │
                                           └─────────────────┘
```

---

## 2. Component Architecture

### 2.1 Frontend Architecture (React)

```
/frontend/src/
│
├── pages/
│   ├── Dashboard.js              # Main landing page
│   │   - Job creation form
│   │   - Active jobs list
│   │   - Job history
│   │
│   ├── JobDetails.js             # Individual job view
│   │   - Progress tracking
│   │   - Video gallery grid
│   │   - Selection interface
│   │
│   └── Settings.js               # Configuration (future)
│
├── components/
│   ├── ui/                       # Shadcn components
│   │   ├── button.jsx
│   │   ├── card.jsx
│   │   ├── checkbox.jsx
│   │   ├── dialog.jsx
│   │   ├── progress.jsx
│   │   └── ...
│   │
│   ├── FileUploader.js           # Drag & drop upload
│   ├── VideoCard.js              # Individual video display
│   ├── VideoGrid.js              # Video gallery layout
│   ├── ProgressBar.js            # Job progress indicator
│   ├── ErrorDisplay.js           # Error message component
│   ├── UpscaleModal.js           # 4K upscaling interface
│   ├── DownloadManager.js        # Batch download handler
│   └── JobStatusBadge.js         # Status indicator
│
├── hooks/
│   ├── useJobPolling.js          # Poll job status
│   ├── useVideoSelection.js      # Manage video selections
│   └── useFileUpload.js          # Handle file uploads
│
├── services/
│   ├── api.js                    # Axios API client
│   └── websocket.js              # Real-time updates (future)
│
└── utils/
    ├── fileParser.js             # Parse prompts file
    ├── validators.js             # Input validation
    └── formatters.js             # Data formatting
```

**State Management:**
- React Context API for global state
- Local component state for UI interactions
- API polling for real-time updates

---

### 2.2 Backend Architecture (FastAPI)

```
/backend/
│
├── server.py                     # Main FastAPI application
│   - CORS configuration
│   - API route registration
│   - Error handlers
│
├── models/
│   ├── job.py                    # Job Pydantic models
│   ├── video.py                  # Video Pydantic models
│   └── session.py                # Session models
│
├── routes/
│   ├── jobs.py                   # Job management endpoints
│   ├── videos.py                 # Video operations endpoints
│   ├── upload.py                 # File upload endpoints
│   └── download.py               # Download endpoints
│
├── services/
│   ├── google_flow_service.py    # ⭐ Core automation logic
│   │   - Browser initialization
│   │   - Login management
│   │   - Project creation
│   │   - Video generation
│   │   - Error handling
│   │
│   ├── video_processor.py        # Video processing
│   │   - Folder parsing
│   │   - Prompt parsing
│   │   - Image-prompt matching
│   │   - Job orchestration
│   │
│   ├── storage_service.py        # Storage management
│   │   - Cloudflare R2 operations
│   │   - Telegram CDN operations
│   │   - File cleanup scheduler
│   │
│   ├── upscaler_service.py       # FFmpeg 4K upscaling
│   │   - Quality presets
│   │   - Progress tracking
│   │   - Batch processing
│   │
│   └── database_service.py       # MongoDB operations
│       - CRUD operations
│       - Query helpers
│
├── utils/
│   ├── playwright_helpers.py     # Browser automation utils
│   ├── file_handlers.py          # File operations
│   ├── validators.py             # Input validation
│   └── logger.py                 # Logging configuration
│
└── config.py                     # Configuration management
    - Environment variables
    - Constants
    - Credentials (mock)
```

---

## 3. Data Flow Architecture

### 3.1 Video Generation Flow

```
┌──────────────┐
│    User      │
│  Uploads     │
│ Images+      │
│  Prompts     │
└──────┬───────┘
       │
       ▼
┌─────────────────────────────────────────┐
│  1. Parse & Validate                    │
│     - Extract images (1.jpeg, 2.jpeg)   │
│     - Parse prompts (prompt_1, prompt_2)│
│     - Match by number                   │
│     - Create job in MongoDB             │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  2. Initialize Playwright Browser       │
│     - Launch headless Chromium          │
│     - Check session cookies             │
│     - Login if needed                   │
└──────────────┬──────────────────────────┘
               │
         ┌─────▼─────┐
         │   Loop    │ For each image-prompt pair
         └─────┬─────┘
               │
   ┌───────────▼────────────┐
   │                        │
   ▼                        ▼
┌──────────────────┐  ┌─────────────────────┐
│ 3a. New Project  │  │ 3b. Configure       │
│    - Create      │  │    - Portrait mode  │
│    - Open        │  │    - 2 outputs      │
│                  │  │    - Veo 3.1 Fast   │
└────────┬─────────┘  └──────────┬──────────┘
         │                       │
         └───────────┬───────────┘
                     ▼
         ┌────────────────────────┐
         │ 4. Upload & Generate   │
         │    - Upload image      │
         │    - Enter prompt      │
         │    - Click generate    │
         └──────────┬─────────────┘
                    │
                    ▼
         ┌────────────────────────┐
         │ 5. Monitor Status      │
         │    Poll every 10s      │
         │    - Generating...     │
         │    - Completed ✓       │
         │    - Error ✗           │
         └──────────┬─────────────┘
                    │
            ┌───────┴────────┐
            │                │
            ▼                ▼
     ┌─────────────┐   ┌──────────────┐
     │  Success    │   │   Error      │
     │             │   │   Handler    │
     └──────┬──────┘   └──────┬───────┘
            │                 │
            │          ┌──────▼────────┐
            │          │  High Demand? │
            │          ├───────────────┤
            │          │ YES: Wait 3min│
            │          │      Retry    │
            │          │ NO:  Return   │
            │          │      error    │
            │          └───────────────┘
            │
            ▼
  ┌──────────────────────┐
  │ 6. Download Videos   │
  │    - Open download   │
  │      menu            │
  │    - Select 720p     │
  │    - Wait download   │
  │    - Get 2 videos    │
  └──────────┬───────────┘
             │
             ▼
  ┌──────────────────────┐
  │ 7. Upload to Storage │
  │    - Cloudflare R2   │
  │    - Telegram CDN    │
  │    - Update DB       │
  └──────────┬───────────┘
             │
             ▼
      ┌──────────────┐
      │  Update UI   │
      │  Show video  │
      └──────────────┘
```

---

### 3.2 Video Selection & Download Flow

```
┌────────────────┐
│ User Selects   │
│ Videos in UI   │
│ (checkboxes)   │
└────────┬───────┘
         │
         ▼
┌─────────────────────────┐
│ Frontend tracks IDs     │
│ [video_1, video_5, ...] │
└──────────┬──────────────┘
           │
     ┌─────▼──────┐
     │   Action   │
     └─────┬──────┘
           │
    ┌──────┴───────┐
    │              │
    ▼              ▼
┌──────────┐  ┌────────────┐
│ Download │  │  Upscale   │
│  720p    │  │   to 4K    │
└────┬─────┘  └─────┬──────┘
     │              │
     ▼              ▼
┌──────────────────────────┐  ┌─────────────────────────┐
│ 1. Fetch from Telegram   │  │ 1. Fetch from Telegram  │
│ 2. Create ZIP            │  │ 2. Run FFmpeg upscaler  │
│ 3. Stream to browser     │  │ 3. Upload 4K to storage │
│ 4. Trigger download      │  │ 4. Update DB            │
│    with folder name      │  │ 5. Enable 4K download   │
└──────────────────────────┘  └─────────────────────────┘
```

---

## 4. Database Schema

### 4.1 MongoDB Collections

**Collection: `jobs`**
```javascript
{
  _id: ObjectId,
  job_name: String,              // User-provided name
  status: String,                // "pending" | "processing" | "completed" | "failed"
  created_at: DateTime,
  updated_at: DateTime,
  total_images: Number,          // 14
  total_prompts: Number,         // 14
  expected_videos: Number,       // 28 (14 images × 2 outputs)
  completed_videos: Number,      // Count of successful generations
  failed_videos: Number,         // Count of failed generations
  current_processing: Number,    // Current image index (1-14)
  images_folder_path: String,    // Temp storage path
  prompts_file_path: String,     // Temp storage path
  error_summary: Array           // List of errors encountered
}
```

**Collection: `videos`**
```javascript
{
  _id: ObjectId,
  job_id: ObjectId,              // Reference to jobs collection
  image_filename: String,        // "1.jpeg"
  prompt_number: Number,         // 1
  prompt_text: String,           // Full prompt
  video_index: Number,           // 1 or 2 (first or second output)
  
  // Generation status
  status: String,                // "queued" | "generating" | "completed" | "failed"
  generation_started_at: DateTime,
  generation_completed_at: DateTime,
  error_message: String,
  error_type: String,            // "high_demand" | "prominent_people" | "policy_violation"
  retry_count: Number,
  
  // Storage URLs
  cloudflare_url: String,        // Temporary R2 URL (2hr TTL)
  telegram_file_id: String,      // Permanent Telegram file ID
  telegram_url: String,          // CDN URL
  local_path_720p: String,       // Temp local path
  
  // 4K upscaling
  upscaled: Boolean,             // false by default
  upscaled_4k_url: String,
  upscaled_telegram_id: String,
  upscale_completed_at: DateTime,
  
  // User actions
  selected_for_download: Boolean, // false by default
  downloaded: Boolean,
  
  // Metadata
  duration_seconds: Number,
  file_size_mb: Number,
  resolution: String,            // "720p" or "4K"
  thumbnail_url: String
}
```

**Collection: `google_flow_sessions`**
```javascript
{
  _id: ObjectId,
  session_active: Boolean,
  cookies: Array,                // Playwright cookies
  user_agent: String,
  last_login_at: DateTime,
  last_used_at: DateTime,
  login_email: String            // "Sameer@techhub.codes"
}
```

---

## 5. API Endpoints Specification

### 5.1 Job Management

**POST `/api/jobs/create`**
- Body: `{ job_name: string }`
- Response: `{ job_id: string, status: "pending" }`

**POST `/api/jobs/{job_id}/upload`**
- Form data: `images_folder` (zip), `prompts_file` (txt)
- Response: `{ uploaded: true, image_count: 14, prompt_count: 14 }`

**POST `/api/jobs/{job_id}/start`**
- Response: `{ started: true, estimated_time_minutes: 120 }`
- Triggers background automation task

**GET `/api/jobs/{job_id}`**
- Response:
  ```json
  {
    "job_id": "...",
    "status": "processing",
    "progress": 0.35,
    "current_image": 5,
    "total_images": 14,
    "completed_videos": 10,
    "failed_videos": 2
  }
  ```

**GET `/api/jobs`**
- Query: `?status=completed&limit=10`
- Response: Array of job summaries

**DELETE `/api/jobs/{job_id}`**
- Cancels active job, deletes data

---

### 5.2 Video Operations

**GET `/api/jobs/{job_id}/videos`**
- Response:
  ```json
  {
    "videos": [
      {
        "video_id": "...",
        "image_filename": "1.jpeg",
        "prompt_number": 1,
        "prompt_text": "...",
        "video_index": 1,
        "status": "completed",
        "cloudflare_url": "...",
        "upscaled": false,
        "selected": false
      }
    ]
  }
  ```

**PUT `/api/videos/{video_id}/select`**
- Body: `{ selected: true }`
- Toggles selection state

**POST `/api/videos/{video_id}/regenerate`**
- Retries generation for failed video
- Body: `{ new_prompt?: string, new_image?: file }`

**POST `/api/videos/upscale`**
- Body: `{ video_ids: [...], quality: "high" }`
- Response: `{ task_id: "..." }`
- Triggers background upscaling

**GET `/api/videos/upscale/{task_id}/status`**
- Response: `{ progress: 0.6, current_video: 3, total_videos: 5 }`

---

### 5.3 Download

**POST `/api/videos/download`**
- Body: `{ video_ids: [...], folder_name: "Project_Final", resolution: "720p" }`
- Response: Stream ZIP file
- Headers: `Content-Disposition: attachment; filename="Project_Final.zip"`

---

## 6. Storage Architecture

### 6.1 Hybrid Storage Strategy

**Cloudflare R2 (Temporary Fast Access)**
- Purpose: Immediate playback in UI
- Retention: 2 hours
- Use case: Active job videos, preview before download

**Telegram CDN (Permanent Storage)**
- Purpose: Long-term archival
- Retention: Indefinite
- Use case: Historical jobs, re-download capability

**Workflow:**
```
Video Generated
      │
      ├─→ Upload to Cloudflare R2 (immediate)
      │   - Return URL to frontend
      │   - User can preview/play
      │
      └─→ Upload to Telegram CDN (background)
          - Get file_id
          - Store in MongoDB
          
After 2 hours:
      └─→ Delete from Cloudflare R2
          - Rely on Telegram for access
```

---

## 7. Browser Automation Details

### 7.1 Playwright Configuration

```python
browser = await playwright.chromium.launch(
    headless=True,
    args=[
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage'
    ]
)

context = await browser.new_context(
    viewport={'width': 1920, 'height': 1080},
    user_agent='Mozilla/5.0 (X11; Linux x86_64) ...'
)
```

### 7.2 Google Flow Interaction Flow

**Login (if needed):**
```
1. Navigate to https://labs.google/fx/tools/flow
2. Check if logged in (look for user profile icon)
3. If not logged in:
   - Click "Sign in"
   - Enter email: Sameer@techhub.codes
   - Enter password: Hhub@#11
   - Handle 2FA if prompted (manual intervention)
4. Save cookies to database
```

**Project Creation:**
```
1. Click "+ New project" button
2. Wait for project interface to load
3. Locate "Frames to Video" option
4. Click to select
```

**Configuration:**
```
1. Find aspect ratio dropdown (default: Landscape)
2. Click dropdown, select "Portrait"
3. Find "Outputs per prompt" field (default: 1)
4. Change to "2"
5. Find model dropdown (default may vary)
6. Select "Veo 3.1 - Fast [Lower Priority]"
```

**Upload & Generate:**
```
1. Locate image upload button
2. Upload reference image (e.g., 1.jpeg)
3. Find prompt textarea
4. Paste prompt text
5. Click "Generate" button
6. Wait for generation (poll status)
```

**Error Detection:**
```
Check for error messages:
- "Flow is experiencing high demand"
  → Retry after 3 minutes
  
- "This prompt might violate our policies about generating prominent people"
  → Return error to user, allow manual edit
  
- "This prompt violates our terms"
  → Return error to user, allow manual edit
```

**Download:**
```
1. Wait for "Download" button to appear
2. Click download button
3. Select quality: "Original size (720p)"
4. Wait for download to complete
5. Move file from downloads folder to temp storage
```

---

## 8. Video Upscaling Architecture

### 8.1 FFmpeg Processing Pipeline

```
Input: 720p video from Telegram CDN
      │
      ▼
┌────────────────────────┐
│  FFmpeg Lanczos Scale  │
│  - Target: 3840×2160   │
│  - Maintain aspect     │
│  - Preserve audio      │
│  - CRF quality preset  │
└──────────┬─────────────┘
           │
           ▼
┌────────────────────────┐
│  Quality Options       │
│  - Fast: CRF 23        │
│  - Balanced: CRF 20    │
│  - High: CRF 18        │
└──────────┬─────────────┘
           │
           ▼
┌────────────────────────┐
│  Output 4K Video       │
│  - Upload to storage   │
│  - Update DB           │
└────────────────────────┘
```

### 8.2 Batch Processing

- Process multiple videos in parallel (max 3 concurrent)
- Show progress bar for each video
- Estimate time remaining
- Allow cancellation

---

## 9. Error Handling Strategy

### 9.1 Error Categories

**Retryable Errors:**
- Network timeouts
- "High demand" from Google Flow
- Temporary storage failures
- **Action**: Auto-retry with exponential backoff

**User-Fixable Errors:**
- Policy violations
- Prominent people detection
- Invalid prompt format
- **Action**: Show error, allow prompt/image edit

**System Errors:**
- Browser crash
- Out of disk space
- Database connection loss
- **Action**: Log error, notify admin, pause job

### 9.2 Recovery Mechanisms

- Save progress after each video
- Resume from last successful image
- Preserve partial results
- Allow manual retry of failed items

---

## 10. Security Considerations

### 10.1 Data Protection
- Temporary file cleanup after job completion
- Secure storage credentials (environment variables)
- No sensitive data in logs
- Rate limiting on API endpoints

### 10.2 Google Flow Session Management
- Rotate sessions periodically
- Handle session expiration gracefully
- Secure cookie storage in database
- Detect and handle captchas/2FA

---

## 11. Performance Optimization

### 11.1 Bottlenecks & Solutions

**Bottleneck**: Video download from Google Flow
- **Solution**: Download in background, show progress

**Bottleneck**: 4K upscaling is CPU-intensive
- **Solution**: Queue system, process in batches

**Bottleneck**: Large file transfers
- **Solution**: Stream downloads, use CDN

### 11.2 Scalability

- Horizontal scaling: Multiple Playwright instances
- Queue-based job processing
- CDN for video delivery
- Database indexing on job_id, status

---

## 12. Monitoring & Logging

### 12.1 Logging Strategy

**Application Logs**: `/app/logs/automation.log`
- Job start/complete events
- Error stack traces
- Performance metrics

**Playwright Logs**: `/app/logs/browser.log`
- Browser console errors
- Navigation events
- Screenshot on failures

**Access Logs**: Nginx/FastAPI logs
- API request/response times
- Error rates

### 12.2 Metrics to Track

- Average time per video generation
- Error rate by error type
- Storage usage
- API response times
- Job success rate

---

## 13. Technology Versions

- **Python**: 3.11+
- **FastAPI**: 0.115+
- **Playwright**: 1.49+
- **FFmpeg**: 6.0+
- **React**: 18.2+
- **MongoDB**: 7.0+
- **Node.js**: 20+

---

## 14. Deployment Architecture

```
┌─────────────────────────────────────────┐
│         Kubernetes Pod                  │
│                                         │
│  ┌────────────────────────────────┐    │
│  │     Supervisor                 │    │
│  │  - Frontend (port 3000)        │    │
│  │  - Backend (port 8001)         │    │
│  └────────────────────────────────┘    │
│                                         │
│  ┌────────────────────────────────┐    │
│  │     Playwright                 │    │
│  │  - Chromium browser            │    │
│  └────────────────────────────────┘    │
│                                         │
│  ┌────────────────────────────────┐    │
│  │     FFmpeg                     │    │
│  │  - Video processing            │    │
│  └────────────────────────────────┘    │
│                                         │
└─────────────────────────────────────────┘
          │                    │
          │                    │
          ▼                    ▼
    ┌──────────┐         ┌───────────┐
    │ MongoDB  │         │ External  │
    │ (local)  │         │ Storage   │
    └──────────┘         │ R2/TG CDN │
                         └───────────┘
```

---

## 15. Future Architecture Enhancements

1. **WebSocket Integration**: Real-time progress updates
2. **Redis Queue**: Better job management
3. **Multi-tenant**: Support multiple users
4. **API Authentication**: JWT tokens
5. **Video Analytics**: Track view counts, popular prompts
6. **Notification Service**: Email/SMS alerts
7. **Backup Strategy**: Automated backups of MongoDB
8. **Monitoring Dashboard**: Grafana/Prometheus

---

This architecture is designed for:
- **Reliability**: Retry mechanisms, error recovery
- **Scalability**: Queue-based processing, CDN storage
- **Maintainability**: Modular services, clear separation of concerns
- **Performance**: Parallel processing, optimized storage
- **User Experience**: Real-time feedback, intuitive interface
