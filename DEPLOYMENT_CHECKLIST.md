# 📋 DEPLOYMENT QUICK CHECKLIST

**Your Database**: ✅ **DONE** (15 queries ran successfully!)

---

## 🚀 STEP 2: Deploy Backend to Render (10-15 min)

Follow: [RENDER_DEPLOYMENT.md](RENDER_DEPLOYMENT.md)

### Quick Checklist:
- [ ] Get DATABASE_URL from Neon
- [ ] Go to render.com
- [ ] Create account with GitHub
- [ ] Click "New +" → "Web Service"
- [ ] Connect your GitHub repo
- [ ] Set Name: `risk-atlas-api`
- [ ] Build: `pip install -r backend/requirements.txt`
- [ ] Start: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
- [ ] Add 8 environment variables (see RENDER_DEPLOYMENT.md)
- [ ] Click "Deploy"
- [ ] Wait 5-10 minutes for deployment
- [ ] Copy backend URL (looks like: `https://risk-atlas-api.onrender.com`)
- [ ] Test /health endpoint → should return JSON ✅

**Time**: ~15 minutes

---

## 🌐 STEP 3: Deploy Frontend to Vercel (5-10 min)

Follow: [VERCEL_DEPLOYMENT.md](VERCEL_DEPLOYMENT.md)

### Quick Checklist:
- [ ] Go to vercel.com
- [ ] Create account with GitHub
- [ ] Click "Add New" → "Project"
- [ ] Import: financial-fraud-detector-saas
- [ ] Set Root Directory: `website`
- [ ] Set Framework: `Other`
- [ ] Leave build commands empty
- [ ] Click "Deploy"
- [ ] Wait 1-2 minutes
- [ ] Copy frontend URL (looks like: `https://risk-atlas.vercel.app`)
- [ ] Verify frontend loads ✅

**Time**: ~10 minutes

---

## 🔗 STEP 4: Connect Frontend ↔ Backend (2 min)

### Option A (Easiest):
1. Open your Vercel URL
2. Find "API Settings" in left sidebar
3. Paste Render backend URL
4. Click Save

### Option B:
1. Update CORS_ORIGINS in Render environment variables
2. Change from `http://localhost:5500` to `https://your-vercel-url.vercel.app`
3. Render auto-redeploys

**Time**: ~2 minutes

---

## ✅ STEP 5: End-to-End Test (5 min)

### Test Your System:
1. [ ] Open frontend URL in browser
2. [ ] Click "Sign Up" → Create account
3. [ ] You should see Firebase auth ✅
4. [ ] Log in
5. [ ] Find "Upload" button
6. [ ] Download `sample_transactions.csv` from repo
7. [ ] Upload CSV file
8. [ ] Wait 10-30 seconds
9. [ ] See fraud detection results! ✅
10. [ ] Check Neon (data stored) ✅

**Time**: ~5 minutes

---

## 📊 TOTAL TIME: ~30-45 minutes

| Step | Time | Status |
|------|------|--------|
| Neon Database | 5 min | ✅ **DONE** |
| Render Backend | 15 min | ⏳ **NEXT** |
| Vercel Frontend | 10 min | ⏭️ Then |
| Connect Them | 2 min | ⏭️ Then |
| End-to-End Test | 5 min | ⏭️ Finally |

---

## 🎯 YOU ARE HERE

```
Neon: ✅✅✅ COMPLETE
       └─ 15 queries ran successfully

Render: ⏳⏳⏳ START NOW
        └─ Follow RENDER_DEPLOYMENT.md

Vercel: ⏭️⏭️⏭️ Next
        └─ Follow VERCEL_DEPLOYMENT.md

Testing: ⏭️⏭️⏭️ Finally
         └─ Follow E2E checklist above
```

---

## 📁 REFERENCE DOCUMENTS

- **RENDER_DEPLOYMENT.md** - Detailed Render setup (step-by-step)
- **VERCEL_DEPLOYMENT.md** - Detailed Vercel setup (step-by-step)
- **NEON_SETUP_REFERENCE.md** - Database queries & reference
- **NEON_INITIALIZATION.md** - Database initialization (already done ✅)
- **DEPLOYMENT_GUIDE.md** - Original comprehensive guide
- **DEPLOYMENT_READY_SUMMARY.md** - Project overview

---

## 🛠️ COMMON ISSUES

**If something fails:**
1. Check the troubleshooting section in the step's document
2. Check Render/Vercel logs (click service → "Logs")
3. Verify all environment variables are set correctly
4. Make sure DATABASE_URL matches exactly

---

## 🚀 READY?

**Next step**: Follow [RENDER_DEPLOYMENT.md](RENDER_DEPLOYMENT.md)

You've got this! 💪

---

**Status**: Ready to Deploy  
**Next**: Render Backend  
**ETA to LIVE**: ~45 minutes from now
