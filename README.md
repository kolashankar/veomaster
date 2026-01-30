# 🎬 VeoMaster - Google Flow Video Automation Platform

A comprehensive video automation platform that streamlines video generation using Google Flow, with integrated storage, upscaling, and management capabilities.

## 🚀 Features

- **Automated Video Generation**: Browser automation for Google Flow
- **Batch Processing**: Handle multiple image-prompt pairs efficiently
- **4K Upscaling**: FFmpeg-powered video upscaling
- **Hybrid Storage**: Cloudflare R2 + Telegram CDN
- **Progress Tracking**: Real-time job monitoring
- **Error Recovery**: Intelligent retry logic for high-demand scenarios

## 📋 Prerequisites

- Python 3.11+
- MongoDB Atlas account
- Cloudflare R2 account
- Telegram Bot credentials
- Google Flow access

## 🔧 Local Setup

### 1. Clone Repository
```bash
git clone https://github.com/kolashankar/veomaster.git
cd veomaster
```

### 2. Backend Setup
```bash
cd backend
pip install -r requirements.txt
playwright install chromium
playwright install-deps
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env` and fill in your credentials:
```bash
cp .env.example .env
# Edit .env with your credentials
```

Required variables:
- `MONGO_URL` - MongoDB connection string
- `DB_NAME` - Database name
- `GOOGLE_FLOW_EMAIL` - Google Flow login email
- `GOOGLE_FLOW_PASSWORD` - Google Flow password
- `CLOUDFLARE_*` - Cloudflare R2 credentials (5 variables)
- `TELEGRAM_*` - Telegram Bot credentials (5 variables)

### 4. Start Backend
```bash
uvicorn server:app --reload --host 0.0.0.0 --port 8001
```

Visit: http://localhost:8001/api/

## 🚀 Deployment to Render

### Quick Deploy

**Build Command:**
```bash
cd backend && pip install --upgrade pip && pip install -r requirements.txt && playwright install chromium && playwright install-deps
```

**Start Command:**
```bash
cd backend && uvicorn server:app --host 0.0.0.0 --port 10000
```

### Environment Variables for Render
Add these in Render Dashboard → Environment:
```
MONGO_URL=<your-mongodb-url>
DB_NAME=veomaster_db
GOOGLE_FLOW_EMAIL=<your-email>
GOOGLE_FLOW_PASSWORD=<your-password>
CLOUDFLARE_ACCOUNT_ID=<your-account-id>
CLOUDFLARE_ACCESS_KEY=<your-access-key>
CLOUDFLARE_SECRET_KEY=<your-secret-key>
CLOUDFLARE_BUCKET_NAME=<your-bucket>
CLOUDFLARE_R2_ENDPOINT=<your-endpoint>
TELEGRAM_API_ID=<your-api-id>
TELEGRAM_API_HASH=<your-api-hash>
TELEGRAM_BOT_TOKEN=<your-bot-token>
TELEGRAM_CHANNEL_ID=<your-channel-id>
TELEGRAM_LOG_CHANNEL=<your-log-channel>
STORAGE_BASE_DIR=/tmp
CORS_ORIGINS=*
```

📖 **Detailed Guide**: See [RENDER_DEPLOYMENT.md](./RENDER_DEPLOYMENT.md)  
⚡ **Quick Reference**: See [DEPLOYMENT_QUICK_REF.md](./DEPLOYMENT_QUICK_REF.md)

### Using Blueprint (render.yaml)
1. Push code to GitHub
2. In Render Dashboard: New → Blueprint
3. Connect repository
4. Add environment variables
5. Deploy!

## 📚 API Documentation

### Health Check
```bash
GET /api/
```

### Create Job
```bash
POST /api/jobs/create
Content-Type: application/json

{
  "job_name": "My Video Project"
}
```

### Upload Files
```bash
POST /api/jobs/{job_id}/upload
Content-Type: multipart/form-data

files: [images + prompts.txt]
```

### Start Generation
```bash
POST /api/jobs/{job_id}/start
```

### Get Job Status
```bash
GET /api/jobs/{job_id}
```

### List Videos
```bash
GET /api/videos/job/{job_id}
```

## 🏗️ Architecture

```
Backend (FastAPI)
├── Models (MongoDB)
│   ├── Job
│   ├── Video
│   └── Session
├── Services
│   ├── Database Service
│   ├── Storage Service (R2 + Telegram)
│   ├── Video Processor
│   ├── Google Flow Service (Playwright)
│   └── Upscaler Service (FFmpeg)
└── Routes
    ├── Jobs API
    └── Videos API
```

## 📁 Project Structure

```
veomaster/
├── backend/
│   ├── config.py              # Configuration (env-based)
│   ├── server.py              # FastAPI application
│   ├── requirements.txt       # Python dependencies
│   ├── .env                   # Credentials (DO NOT COMMIT)
│   ├── .env.example          # Template for credentials
│   ├── models/               # Data models
│   ├── services/             # Business logic
│   ├── routes/               # API endpoints
│   └── utils/                # Utilities
├── render.yaml               # Render deployment config
├── RENDER_DEPLOYMENT.md      # Deployment guide
├── DEPLOYMENT_QUICK_REF.md   # Quick reference
├── SECURITY_FIXES_SUMMARY.md # Recent security improvements
└── README.md                 # This file
```

## 🔒 Security Notes

- ✅ All credentials stored in environment variables
- ✅ No hardcoded secrets in code
- ✅ `.env` files excluded from git
- ✅ Input validation on all endpoints
- ✅ Secure storage with R2 and Telegram

## 🐛 Troubleshooting

### Permission Denied Errors
If you encounter permission errors on deployment:
- Set `STORAGE_BASE_DIR=/tmp` in environment variables
- This is automatically handled in the configuration

### MongoDB Connection Issues
- Verify connection string format
- Check Network Access in MongoDB Atlas (allow 0.0.0.0/0)
- Ensure credentials are correct

### Playwright/Chromium Issues
- Verify build command includes `playwright install chromium`
- Check that `playwright install-deps` ran successfully
- Review build logs for system dependency errors

## 📊 Status

- ✅ Backend API Complete
- ✅ Automation Services Complete
- ✅ Database Integration Complete
- ✅ Storage Integration Complete
- ✅ Security Hardening Complete
- ✅ Deployment Ready

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## 📄 License

This project is private and confidential.

## 📞 Support

For issues or questions:
- Check [RENDER_DEPLOYMENT.md](./RENDER_DEPLOYMENT.md) for deployment help
- Review [SECURITY_FIXES_SUMMARY.md](./SECURITY_FIXES_SUMMARY.md) for recent changes
- Check application logs in Render dashboard

---

**Version:** 1.0.0  
**Last Updated:** January 30, 2025  
**Status:** Production Ready ✅
