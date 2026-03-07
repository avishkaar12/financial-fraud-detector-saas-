# 🌐 VERCEL DEPLOYMENT - Step by Step

**Time Required**: 5-10 minutes  
**Difficulty**: Easy ✅  
**Status**: Ready to Deploy (after Render is live)

---

## STEP 1: Create Vercel Account (if needed)

1. Go to [vercel.com](https://vercel.com)
2. Click **"Sign Up"** (top right)
3. Use GitHub account (recommended)
4. Authorize Vercel to access your GitHub repos
5. You'll be redirected to dashboard

---

## STEP 2: Import Your Repository

1. In Vercel dashboard, click **"Add New"** (top left)
2. Click **"Project"**
3. Click **"Continue with GitHub"**
4. Search for: **financial-fraud-detector-saas**
5. Click **"Import"**

---

## STEP 3: Configure Project Settings

You'll see a configuration page:

### Root Directory
```
website
```
(Click change → type "website" → confirm)

### Framework Preset
```
Other (since it's static site)
```

### Build Command
```
(leave empty)
```

### Output Directory
```
.
```
(or leave empty)

### Install Command
```
(leave empty)
```

---

## STEP 4: Deploy!

1. Click **"Deploy"** (blue button bottom right)
2. Wait 1-2 minutes
3. You'll see **"Congratulations! Your project has been successfully deployed"** ✅

---

## STEP 5: Get Your Vercel Frontend URL

1. After deployment, you'll see a URL like:
   ```
   https://risk-atlas.vercel.app
   ```
2. **Copy this URL** - you'll need it

---

## STEP 6: Connect Frontend to Backend

### Option A: In Frontend UI (Easiest)
1. Open your Vercel URL in browser
2. Click **"API Settings"** (left sidebar)
3. Paste your Render backend URL:
   ```
   https://your-render-service.onrender.com
   ```
4. Click **"Save"**

### Option B: Update Environment Variable
1. In Vercel dashboard, go to project settings
2. Click **"Environment Variables"**
3. Add variable:
   - **Name**: `REACT_APP_API_BASE`
   - **Value**: `https://your-render-service.onrender.com`
4. Click **"Add"**
5. Redeploy

---

## STEP 7: Verify Frontend is Working

1. Open your Vercel URL in browser
2. You should see **"Risk Atlas"** landing page
3. Click **"Sign In"** or **"Sign Up"**
4. You should see Firebase authentication form
5. Enter email and password
6. You should be logged in! ✅

---

## STEP 8: Test Upload Feature

1. Click **"Sign In"** and log in
2. Click **"Upload"** (or equivalent button)
3. Download `sample_transactions.csv` from your repo
4. Upload the file
5. Wait 10-30 seconds
6. You should see fraud detection results! ✅

---

## STEP 9: Update Render CORS (Important!)

Now that Vercel is live, update Render to allow it:

1. Go to [render.com](https://render.com)
2. Click on **"risk-atlas-api"** service
3. Click **"Environment"** (top navigation)
4. Find **"CORS_ORIGINS"** variable
5. Change value to:
   ```
   https://your-vercel-url.vercel.app
   ```
6. Click **"Save Changes"**
7. Service will automatically redeploy

---

## ❌ Troubleshooting

### "Blank page / site won't load"
- Check browser console for errors (F12)
- Check Firebase config is populated in `website/firebase-config.js`
- Verify API Base URL is set correctly

### "Firebase auth not working"
- Go to [firebase.google.com](https://firebase.google.com)
- Check if your domain is in whitelist
- Add your Vercel URL to Firebase allowed domains:
  1. Firebase Console → risk-atlas-9d5a6
  2. Authentication → Settings
  3. Add `https://your-vercel-url.vercel.app` to whitelist

### "Upload fails / no results"
- Check browser console for errors
- Check Render backend is running (visit /health)
- Verify CORS_ORIGINS includes Vercel URL
- Check Neon database has tables (run verification queries)

### "Upload says 'API error'"
- Check Render logs for the actual error
- Verify DATABASE_URL is correct in Render
- Try uploading from same network first (no firewall issues)

### "Dashboard shows loading forever"
- Check Render /health endpoint
- Verify API Base URL in frontend
- Check browser console for CORS errors

---

## 🎯 You're Done with Vercel! ✅

Your frontend is now **live on the internet**!

---

## 📊 What You Now Have

```
✅ Frontend deployed on Vercel
✅ Connected to Render backend API
✅ Firebase authentication working
✅ Upload feature ready
✅ Dashboards accessible
```

---

## 🔗 End-to-End Test

### Complete Flow Test:
1. ✅ Open Vercel URL
2. ✅ Sign up / Sign in
3. ✅ Upload sample_transactions.csv
4. ✅ See fraud predictions
5. ✅ Check Neon database (fraud data stored)
6. ✅ View dashboards and alerts

If all 6 work → **You're LIVE!** 🎉

---

## 📋 Your Production URLs

| Component | Type | Status | URL |
|-----------|------|--------|-----|
| Backend API | Render | 🟢 Live | `https://risk-atlas-api.onrender.com` |
| Frontend | Vercel | 🟢 Live | `https://risk-atlas.vercel.app` |
| Database | Neon | 🟢 Live | PostgreSQL pooled connection |
| Auth | Firebase | 🟢 Live | risk-atlas-9d5a6 |

---

## 🚀 Monitoring Your System

### Check Backend Health
```
https://your-render-url.onrender.com/health
```

### View Render Logs
- Render dashboard → Service → "Logs"

### View Vercel Logs
- Vercel dashboard → Project → "Deployments" → "Logs"

### Monitor Database
- Neon console → SQL Editor
- Run: `SELECT COUNT(*) FROM transactions;`

---

## 📈 Next Steps (Optional)

1. **Set up error monitoring** - Sentry or similar
2. **Enable analytics** - Track user behavior
3. **Add email notifications** - For high-severity alerts
4. **Set up auto-scaling** - If traffic increases
5. **Implement backup strategy** - Database backups

---

**Status**: ✅ Production Live  
**Time to Live**: ~30 minutes total  
**You Did It!** 🎉
