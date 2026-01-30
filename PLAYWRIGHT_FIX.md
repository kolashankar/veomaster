# 🎭 Playwright Installation Fix for Render

## Problem

Your deployment failed with this error:
```
Installing dependencies...
Switching to root user to install dependencies...
Password: su: Authentication failure
Failed to install browser dependencies
Error: Installation process exited with code: 1
```

## Root Cause

The `playwright install-deps` command tries to install system-level dependencies (like graphics libraries, fonts, etc.) which requires root/sudo access. Render's standard Python environment **does not allow root access** for security reasons.

## ✅ Solution

**Remove** `playwright install-deps` from your build command. Render's Python environment already includes most dependencies that Chromium needs.

### Updated Build Command

**❌ OLD (Causes Failure):**
```bash
cd backend && pip install --upgrade pip && pip install -r requirements.txt && playwright install chromium && playwright install-deps
```

**✅ NEW (Works on Render):**
```bash
cd backend && pip install --upgrade pip && pip install -r requirements.txt && playwright install chromium
```

## Why This Works

1. **Render Pre-installs Dependencies**: Render's Python environment comes with most system libraries that Chromium needs:
   - `libnss3`
   - `libatk-bridge2.0-0`
   - `libdrm2`
   - `libxkbcommon0`
   - `libgbm1`
   - And many more...

2. **Chromium Headless Mode**: Your application runs Chromium in headless mode, which has fewer system dependencies than the full browser.

3. **Playwright is Smart**: Playwright will work with available system libraries and gracefully handle missing ones in headless mode.

## Implementation Steps

### Option 1: Update render.yaml (Recommended)

Your `render.yaml` has been updated. Just redeploy:

1. Push updated `render.yaml` to GitHub
2. Render will auto-detect changes
3. Redeploy your service

### Option 2: Update Manually in Render Dashboard

1. Go to your service in Render Dashboard
2. Navigate to "Settings"
3. Find "Build Command"
4. Update to:
   ```bash
   cd backend && pip install --upgrade pip && pip install -r requirements.txt && playwright install chromium
   ```
5. Save and trigger manual deploy

## Additional Configuration

Add this environment variable to improve Playwright stability on Render:

```
PLAYWRIGHT_SKIP_BROWSER_GC=1
```

This disables browser garbage collection which can cause issues in containerized environments.

## Verification

After deployment, check your logs for:

```
✅ Chromium downloaded successfully
✅ Google Flow Video Automation Platform STARTING
✅ Phase 1: Foundation - Database, Models, Storage initialized
```

## Alternative: Docker Deployment

If you absolutely need `playwright install-deps` (for specific dependencies), you'll need to use Render's Docker deployment:

1. Create a `Dockerfile`:
```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy backend files
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright with dependencies (works in Docker)
RUN playwright install chromium
RUN playwright install-deps

COPY backend/ .

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "10000"]
```

2. Deploy as Docker service instead of Python service

**Note**: Docker deployment requires a paid Render plan.

## Testing Locally

To test if Playwright works without system dependencies:

```bash
# Install without deps
playwright install chromium

# Test browser launch
python -c "from playwright.sync_api import sync_playwright; \
with sync_playwright() as p: \
    browser = p.chromium.launch(headless=True); \
    print('✅ Browser launched successfully'); \
    browser.close()"
```

## Common Issues After Fix

### Issue: Browser fails to launch
**Solution**: Add environment variables:
```
PLAYWRIGHT_SKIP_BROWSER_GC=1
PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH=/opt/render/.cache/ms-playwright/chromium-*/chrome-linux/chrome
```

### Issue: Fonts missing
**Solution**: Use web-safe fonts or include font files in your project. Render has basic fonts installed.

### Issue: Screenshot/PDF issues
**Solution**: These usually work fine in headless mode. If issues persist, consider Docker deployment.

## Summary

✅ **DO**: Use `playwright install chromium`  
❌ **DON'T**: Use `playwright install-deps` on standard Render Python environment  
🐳 **ALTERNATIVE**: Use Docker deployment if you need full control over system dependencies  

## Updated Files

The following files have been updated with the fix:
- ✅ `render.yaml` - Removed `playwright install-deps`
- ✅ `DEPLOYMENT_QUICK_REF.md` - Updated build command
- ✅ This file (`PLAYWRIGHT_FIX.md`) - Complete explanation

---

**Your next step**: Redeploy on Render with the updated build command. The deployment should now succeed! 🚀
