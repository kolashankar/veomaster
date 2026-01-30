# Quick Deployment Reference for Render

## 🚀 Quick Start Commands

### Build Command (FIXED - No install-deps)
```bash
cd backend && pip install --upgrade pip && pip install -r requirements.txt && playwright install chromium
```

⚠️ **IMPORTANT**: Do NOT include `playwright install-deps` - it requires root access which Render doesn't provide.

### Start Command
```bash
cd backend && uvicorn server:app --host 0.0.0.0 --port 10000
```

### Root Directory
```
. (project root)
```

## 📋 Required Environment Variables

Copy these values from your `.env` file and add them in Render's Environment tab:

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
PLAYWRIGHT_SKIP_BROWSER_GC=1
```

## ⚙️ Service Configuration

| Setting | Value |
|---------|-------|
| **Environment** | Python 3 |
| **Python Version** | 3.11+ |
| **Region** | Oregon (or closest to you) |
| **Plan** | Starter or higher |
| **Health Check Path** | `/api/` |
| **Port** | 10000 (auto-configured) |

## 🔍 Health Check

After deployment, verify at:
```
https://your-service-name.onrender.com/api/
```

Expected response:
```json
{
  "message": "Google Flow Video Automation Platform API",
  "status": "running",
  "version": "1.0.0"
}
```

## 📝 Important Notes

1. **Playwright Dependencies**: Render's Python environment already includes most system dependencies needed by Chromium
2. **No Root Access**: `playwright install-deps` won't work because it needs root access
3. **Storage**: All temporary files use `/tmp` directory (automatically handled)
4. **Secrets**: Never commit `.env` file to git
5. **Logs**: Available in Render dashboard under "Logs" tab

## 🔧 Troubleshooting Quick Fixes

### Build fails with "su: Authentication failure"
**Solution**: Remove `playwright install-deps` from build command. Use only:
```bash
playwright install chromium
```

### Browser automation fails
**Solution**: 
1. Set `PLAYWRIGHT_SKIP_BROWSER_GC=1` in environment variables
2. Render's environment has most dependencies pre-installed
3. If issues persist, consider upgrading to a paid plan with Docker support

### Application won't start
- Verify all environment variables are set
- Check MongoDB Atlas network access (allow 0.0.0.0/0)
- Review startup logs for missing credentials

### Permission errors
- Ensure STORAGE_BASE_DIR=/tmp is set
- This is required for Render's filesystem

## 📚 Full Documentation

For detailed instructions, see: [RENDER_DEPLOYMENT.md](./RENDER_DEPLOYMENT.md)

---
**Quick Tip**: Use Render's Blueprint feature with `render.yaml` for one-click deployment!
