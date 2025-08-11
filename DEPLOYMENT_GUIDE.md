# 🚀 Deployment Guide - Dhaan Trading System

## Current Issue
- ✅ **Frontend deployed**: Vercel (dhaan-nu.vercel.app)
- ❌ **Backend not deployed**: Still running locally
- 🔥 **Result**: 404 errors because frontend can't reach backend

## Quick Deployment Solutions

### Option 1: Railway (Recommended) 🚀

1. **Create Railway Account**: https://railway.app
2. **Deploy Backend**:
   ```bash
   # Install Railway CLI
   npm install -g @railway/cli
   
   # Login and deploy
   railway login
   railway deploy
   ```
3. **Get Backend URL**: Copy the Railway app URL (e.g., `https://dhaan-backend-production.up.railway.app`)

### Option 2: Render 🌐

1. **Create Render Account**: https://render.com
2. **Connect GitHub**: Link your repository
3. **Create Web Service**:
   - Build Command: `pip install -r requirements-prod.txt`
   - Start Command: `cd backend && python app.py`
4. **Get Backend URL**: Copy the Render app URL

### Option 3: Heroku 🔧

1. **Create Heroku Account**: https://heroku.com
2. **Deploy with Heroku CLI**:
   ```bash
   # Install Heroku CLI and login
   heroku create dhaan-backend
   git push heroku main
   ```

## Update Frontend Configuration

Once backend is deployed, update the frontend API URL:

### File: `frontend/src/services/api.ts`
```typescript
// Change this line:
const API_BASE_URL = 'http://localhost:8000';

// To your deployed backend URL:
const API_BASE_URL = 'https://your-backend-url.railway.app';
```

### Redeploy Frontend
```bash
cd frontend
npm run build
# Push to Vercel (automatic deployment)
```

## Environment Variables

Set these in your deployment platform:

```env
DHAN_CLIENT_ID=1107931059
DHAN_ACCESS_TOKEN=your_valid_token_here
PORT=8000
FLASK_ENV=production
```

## Testing Deployment

1. **Backend Health Check**: `https://your-backend-url/api/dashboard`
2. **Frontend Access**: `https://dhaan-nu.vercel.app`
3. **Full Functionality**: Navigate to Strategy Testing page

## Quick Fix (Temporary)

**For immediate testing**, you can run both locally:

1. **Backend**: `cd backend && python app.py` (port 8000)
2. **Frontend**: `cd frontend && npm start` (port 3000)
3. **Access**: http://localhost:3000

## Files Ready for Deployment

- ✅ `railway.toml` - Railway configuration
- ✅ `Procfile` - Process configuration
- ✅ `requirements-prod.txt` - Production dependencies
- ✅ `backend/app.py` - Production-ready Flask app

## Next Steps

1. Choose deployment platform (Railway recommended)
2. Deploy backend using guide above
3. Update frontend API URL
4. Test complete system
5. Update Dhan API token when available

**Total setup time: ~10 minutes** ⚡️ 