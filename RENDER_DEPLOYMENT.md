# 🚀 RENDER DEPLOYMENT - Step by Step

**Time Required**: 10-15 minutes  
**Difficulty**: Easy ✅  
**Status**: Ready to Deploy

---

## STEP 1: Get Your DATABASE_URL from Neon

1. Go to [neon.tech](https://neon.tech)
2. Click on your project: **risk-atlas-9d5a6**
3. Click **"Connection"** (top right)
4. Under "Pooled Connection", copy the entire connection string
5. It looks like:
   ```
   postgresql://neondb_owner:npg_Pj8lpBs0YLib@ep-nameless-leaf-aic9mhib-pooler.c-4.us-east-1.aws.neon.tech/neondb?sslmode=require
   ```
6. **Save this** - you'll need it in Render

---

## STEP 2: Create Render Account (if needed)

1. Go to [render.com](https://render.com)
2. Click **"Sign Up"** (top right)
3. Use GitHub account to sign up (recommended)
4. Authorize Render to access your GitHub repos
5. You'll be redirected to dashboard

---

## STEP 3: Connect GitHub to Render

1. In Render dashboard, click **"New +"** (top right)
2. Click **"Web Service"**
3. Click **"Connect a repository"**
4. Select your GitHub account
5. Find and click on: **financial-fraud-detector-saas**
6. Click **"Connect"**

---

## STEP 4: Configure Render Service

After connecting the repo, you'll see a form:

### Name
```
risk-atlas-api
```

### Environment
```
Python 3
```

### Build Command
```
pip install -r backend/requirements.txt
```

### Start Command
```
uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

### Plan
```
Free (good enough to start)
```

### Region
```
Oregon (closest to Neon)
```

---

## STEP 5: Add Environment Variables

After you click "Create Web Service", you'll be taken to the deployment page.

Scroll down to **"Environment"** section and add these variables:

### Variable 1: DATABASE_URL
- **Key**: `DATABASE_URL`
- **Value**: [Paste the full connection string from Neon]
  ```
  postgresql://neondb_owner:npg_Pj8lpBs0YLib@ep-nameless-leaf-aic9mhib-pooler.c-4.us-east-1.aws.neon.tech/neondb?sslmode=require
  ```

### Variable 2: DB_SSLMODE
- **Key**: `DB_SSLMODE`
- **Value**: `require`

### Variable 3: AUTH_REQUIRED
- **Key**: `AUTH_REQUIRED`
- **Value**: `true`

### Variable 4: FIREBASE_SERVICE_ACCOUNT_JSON
- **Key**: `FIREBASE_SERVICE_ACCOUNT_JSON`
- **Value**: [Copy from .env.render - the long JSON]
  ```
  {"type":"service_account","project_id":"risk-atlas-9d5a6",...}
  ```

### Variable 5: CORS_ORIGINS
- **Key**: `CORS_ORIGINS`
- **Value**: `http://localhost:5500,http://127.0.0.1:5500`
  (We'll update this after Vercel deployment)

### Variable 6: CORS_ORIGIN_REGEX
- **Key**: `CORS_ORIGIN_REGEX`
- **Value**: 
  ```
  ^https?://(localhost|127\.0\.0\.1)(:\d+)?$|^https://.*\.vercel\.app$|^vscode-webview://.*$|^null$
  ```

### Variable 7: MAX_DETECT_ROWS
- **Key**: `MAX_DETECT_ROWS`
- **Value**: `50000`

### Variable 8: MAX_SHAP_EXPLANATIONS
- **Key**: `MAX_SHAP_EXPLANATIONS`
- **Value**: `40`

---

## STEP 6: Deploy!

1. After adding all environment variables, click **"Deploy"** (bottom right)
2. You'll see deployment logs streaming
3. Wait 5-10 minutes for deployment to complete
4. You'll see: **"Your service is live"** ✅

---

## STEP 7: Get Your Render Backend URL

1. After deployment completes, you'll see a URL like:
   ```
   https://risk-atlas-api.onrender.com
   ```
2. **Copy this URL** - you'll need it for Vercel frontend

---

## STEP 8: Verify Backend is Working

**Check the health endpoint:**

1. Copy your Render URL
2. Open in browser:
   ```
   https://your-render-service.onrender.com/health
   ```
3. You should see:
   ```json
   {
     "status": "ok",
     "model": "loaded",
     "threshold": 0.5,
     "auth_required": true,
     "db_configured": true
   }
   ```

**If you see this → Backend is LIVE!** ✅

---

## ❌ Troubleshooting

### "Build failed"
- Check build logs (scroll up in deployment page)
- Ensure `backend/requirements.txt` exists
- Try redeploying by clicking "Redeploy"

### "Cannot connect to database"
- Verify DATABASE_URL is correctly copied (no typos)
- Check Neon is running (go to neon.tech dashboard)
- Ensure IP whitelist allows Render (should be automatic)

### "/health returns 500"
- Check Render logs: Click service → "Logs" (top right)
- Look for error messages
- Common: Firebase service account JSON formatting

### "Application startup failed"
- Check uvicorn is running correctly
- Verify `backend/main.py` exists
- Check for import errors in logs

### Can't reach the URL
- Render free tier goes to sleep after 15 minutes
- Just refresh the page (takes 30 seconds to wake up)
- Upgrade to paid plan to avoid this

---

## 🎯 You're Done with Render! ✅

Your backend is now **live on the internet**!

**Next steps:**
1. ✅ Neon database: **DONE**
2. ✅ Render backend: **DONE**
3. ⏭️ Vercel frontend: Deploy next
4. ⏭️ Connect frontend to backend
5. ⏭️ End-to-end test

---

## 📊 What You Now Have

```
✅ Backend API running on Render
✅ Connected to Neon database
✅ Firebase authentication enabled
✅ ML model loaded and ready
✅ CORS configured for frontend
✅ Health check passing
```

---

## 🚀 Next: Deploy Frontend to Vercel

Once backend is confirmed working:
1. Go to [vercel.com](https://vercel.com)
2. Create account with GitHub
3. Import this repository
4. Set root directory to `website/`
5. Deploy!

Then update CORS_ORIGINS in Render to your Vercel URL.

---

**Status**: Ready to Deploy  
**Next**: Deploy to Vercel  
**Time Estimate**: 15 minutes for this step
