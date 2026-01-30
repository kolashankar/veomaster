# ✅ Render Deployment Checklist

## Pre-Deployment Checklist

### 1. Code Preparation
- [x] Fixed permission errors (changed `/app` to configurable paths)
- [x] Removed hardcoded credentials from code
- [x] All credentials in `.env` file
- [x] Created `.env.example` template
- [x] Updated `.gitignore` for security
- [x] Created `render.yaml` deployment config
- [x] Documentation complete

### 2. Credentials Verification
- [x] MongoDB connection string ready
- [x] Google Flow credentials ready
- [x] Cloudflare R2 credentials ready (5 variables)
- [x] Telegram Bot credentials ready (5 variables)
- [x] All credentials tested locally

### 3. Local Testing (Optional but Recommended)
```bash
# Test configuration
cd backend
python -c "from config import MONGO_URL, DB_NAME; print('✓ Config OK')"

# Test with /tmp (simulates Render)
STORAGE_BASE_DIR=/tmp python -c "from config import TEMP_UPLOAD_DIR; print('✓ Paths OK')"

# Test server startup
uvicorn server:app --port 8001 &
sleep 5
curl http://localhost:8001/api/
```

## Deployment Steps

### Option A: Using render.yaml (Recommended)

#### Step 1: Push to GitHub
```bash
git add .
git commit -m "Ready for Render deployment"
git push origin main
```

#### Step 2: Create Blueprint on Render
1. Go to https://dashboard.render.com
2. Click "New +" → "Blueprint"
3. Connect your GitHub repository: `kolashankar/veomaster`
4. Render detects `render.yaml` automatically
5. Click "Apply"

#### Step 3: Add Environment Variables
In Render Dashboard → Your Service → Environment:

Copy-paste from your `.env` file:
```
MONGO_URL=mongodb+srv://shankarkola9999_db_user:Z9hG1GUl5gGWFbcD@veomaster.3qiiqox.mongodb.net/veomaster_db?appName=veomaster
DB_NAME=veomaster_db
GOOGLE_FLOW_EMAIL=Sameer@techhub.codes
GOOGLE_FLOW_PASSWORD=Hhub@#11
GOOGLE_FLOW_URL=https://labs.google/fx/tools/flow
CLOUDFLARE_ACCOUNT_ID=41122f37e46172b1285208644a485a1a
CLOUDFLARE_ACCESS_KEY=49790997dfd89cf4a8313bdcca783799
CLOUDFLARE_SECRET_KEY=af4aef462be7f4ff633f41ad64ffdc7d636dbd54b593f45ef63581df3ea388f1
CLOUDFLARE_BUCKET_NAME=veobucket
CLOUDFLARE_R2_ENDPOINT=https://41122f37e46172b1285208644a485a1a.r2.cloudflarestorage.com
CLOUDFLARE_R2_TTL_HOURS=2
TELEGRAM_API_ID=24271861
TELEGRAM_API_HASH=fc5e782b934ed58b28780f41f01ed024
TELEGRAM_BOT_TOKEN=8558426167:AAG4La94aYLmg-HJnjIvarf2T-bciHdWHGU
TELEGRAM_CHANNEL_ID=-1003779605786
TELEGRAM_LOG_CHANNEL=-1003836225813
CORS_ORIGINS=*
STORAGE_BASE_DIR=/tmp
```

⚠️ **CRITICAL**: Don't forget `STORAGE_BASE_DIR=/tmp`

#### Step 4: Deploy
- Click "Create Web Service" or "Deploy"
- Wait 5-10 minutes for build to complete
- Monitor build logs for any issues

### Option B: Manual Setup

#### Step 1: Create Web Service
1. Render Dashboard → "New +" → "Web Service"
2. Connect GitHub → Select `kolashankar/veomaster`
3. Configure:
   - **Name**: veomaster-backend
   - **Region**: Oregon (or closest to you)
   - **Branch**: main
   - **Root Directory**: (leave empty)
   - **Environment**: Python 3
   - **Build Command**:
     ```
     cd backend && pip install --upgrade pip && pip install -r requirements.txt && playwright install chromium
     ```
     ⚠️ **IMPORTANT**: Do NOT include `playwright install-deps` - it requires root access!
   - **Start Command**:
     ```
     cd backend && uvicorn server:app --host 0.0.0.0 --port 10000
     ```

#### Step 2: Add Environment Variables
Same as Option A, Step 3

#### Step 3: Advanced Settings
- **Health Check Path**: `/api/`
- **Auto-Deploy**: Yes (optional)

#### Step 4: Create Web Service
- Click "Create Web Service"
- Monitor deployment

## Post-Deployment Verification

### Step 1: Check Service Status
In Render Dashboard:
- [ ] Build completed successfully
- [ ] Service is "Live" (green)
- [ ] No error logs

### Step 2: Test Health Endpoint
```bash
curl https://your-service-name.onrender.com/api/
```

Expected response:
```json
{
  "message": "Google Flow Video Automation Platform API",
  "status": "running",
  "version": "1.0.0"
}
```

### Step 3: Test API Functionality
```bash
# Create a test job
curl -X POST https://your-service-name.onrender.com/api/jobs/create \
  -H "Content-Type: application/json" \
  -d '{"job_name": "Test Job"}'
```

Expected: Job created with ID

### Step 4: Check Logs
In Render Dashboard → Logs tab:
- [ ] No startup errors
- [ ] Database connected successfully
- [ ] All services initialized
- [ ] Correct storage paths (`/tmp/...`)

### Step 5: Verify MongoDB Connection
Check logs for:
```
✅ Phase 1: Foundation - Database, Models, Storage initialized
```

### Step 6: Test Endpoints
- [ ] GET /api/ (health check)
- [ ] POST /api/jobs/create
- [ ] GET /api/jobs
- [ ] All returning 200 OK

## Common Issues & Solutions

### ❌ Build Fails

**Symptom**: Build process fails with dependency errors

**Solutions**:
1. Check Python version (should be 3.11+)
2. Verify `requirements.txt` is in backend folder
3. Check build logs for specific package errors
4. Ensure playwright commands are in build command

### ❌ Permission Denied

**Symptom**: `PermissionError: [Errno 13] Permission denied: '/app'`

**Solutions**:
1. Ensure `STORAGE_BASE_DIR=/tmp` in environment variables
2. Verify config.py is using environment-based paths
3. Check that you pushed latest code with fixes

### ❌ Application Won't Start

**Symptom**: Service shows "Deploy failed" or crashes on startup

**Solutions**:
1. Check all environment variables are set
2. Verify MongoDB connection string is correct
3. Ensure MongoDB Atlas allows connections from `0.0.0.0/0`
4. Review startup logs for missing credentials
5. Verify all required credentials are present

### ❌ Health Check Fails

**Symptom**: Service marked as unhealthy

**Solutions**:
1. Ensure Health Check Path is `/api/` (with trailing slash)
2. Check if application is binding to correct port (10000)
3. Verify server is starting successfully in logs
4. Test endpoint manually with curl

### ❌ Database Connection Error

**Symptom**: "Failed to connect to MongoDB" in logs

**Solutions**:
1. Verify MONGO_URL is correct and properly formatted
2. Check MongoDB Atlas Network Access:
   - Go to Atlas Dashboard
   - Network Access → Add IP Address
   - Add `0.0.0.0/0` (allow from anywhere)
3. Verify database credentials are correct
4. Test connection string locally first

### ❌ Playwright/Chromium Error

**Symptom**: Browser automation fails

**Solutions**:
1. Ensure build command includes: `playwright install chromium`
2. Add: `playwright install-deps` for system dependencies
3. Check Render plan supports required resources
4. Review logs for specific Playwright errors

## Monitoring & Maintenance

### Regular Checks
- [ ] Monitor error rates in Render dashboard
- [ ] Check disk usage (temp files in `/tmp`)
- [ ] Review application logs weekly
- [ ] Monitor database performance

### Logs Access
```bash
# In Render Dashboard
Services → Your Service → Logs

# Look for:
- Startup messages
- API requests
- Error messages
- Database connections
```

### Metrics to Watch
- Response times
- Error rates
- Memory usage
- CPU usage

## Rollback Procedure

If deployment fails:

1. **Via Render Dashboard**:
   - Go to your service
   - Click "Deploys" tab
   - Find last working deployment
   - Click "Redeploy"

2. **Via Git**:
   ```bash
   git revert HEAD
   git push origin main
   ```

## Security Post-Deployment

- [ ] Verify `.env` is NOT in repository
- [ ] Confirm credentials are only in Render environment
- [ ] Update CORS_ORIGINS to specific domain (not `*`) if needed
- [ ] Review access logs periodically
- [ ] Rotate credentials every 90 days

## Support Resources

- **Render Documentation**: https://render.com/docs
- **MongoDB Atlas Support**: https://www.mongodb.com/docs/atlas/
- **Playwright Documentation**: https://playwright.dev/python/
- **Project Documentation**:
  - [RENDER_DEPLOYMENT.md](./RENDER_DEPLOYMENT.md) - Detailed guide
  - [DEPLOYMENT_QUICK_REF.md](./DEPLOYMENT_QUICK_REF.md) - Quick reference
  - [SECURITY_FIXES_SUMMARY.md](./SECURITY_FIXES_SUMMARY.md) - Security changes

## Final Checklist

Before considering deployment complete:

- [ ] Service is "Live" in Render
- [ ] Health check passing
- [ ] API responds correctly
- [ ] Database connection working
- [ ] No errors in logs
- [ ] Test job creation works
- [ ] All endpoints responding
- [ ] Storage paths using `/tmp`
- [ ] Environment variables all set
- [ ] Documentation reviewed

## Success Criteria

✅ **Deployment is successful when:**
1. Service shows "Live" status
2. Health endpoint returns correct response
3. Can create and retrieve jobs via API
4. No permission errors in logs
5. Database operations work
6. All environment variables loaded
7. Storage directories created in `/tmp`

---

**Status After Completion**: 🎉 PRODUCTION READY

**Estimated Deployment Time**: 10-15 minutes

**Support Contact**: Check Render dashboard for issues
