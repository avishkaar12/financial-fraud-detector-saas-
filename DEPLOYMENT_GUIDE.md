# 🚀 COMPLETE DEPLOYMENT GUIDE - Risk Atlas

**Status**: Production-Ready (March 7, 2026)  
**Tech Stack**: Render + Vercel + Neon + Firebase

---

## **STEP 1: Database Schema - Neon** 📊

### 1.1 Create Neon Project (if not already done)
- Go to [neon.tech](https://neon.tech)
- Create a new project
- Copy the **pooled connection** URI

### 1.2 Initialize Database Schema
- In Neon SQL Editor, run contents of `db_schema.sql`
- Creates 3 tables: `transactions`, `model_logs`, `alerts`
- Includes indexes for performance
- Run verification query to confirm

✅ **Verify**: Run in Neon SQL Editor:
```sql
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' AND table_name IN ('transactions', 'model_logs', 'alerts');
```

**Expected Result**: 3 rows (transactions, model_logs, alerts)

---

## **STEP 2: Backend Deployment - Render** ⚙️

### 2.1 Connect Repository to Render
1. Go to [render.com](https://render.com)
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Select this repo → Branch: `main`

### 2.2 Configure Render Service
- **Name**: `risk-atlas-api`
- **Runtime**: Python 3
- **Build Command**: `pip install -r backend/requirements.txt`
- **Start Command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
- **Plan**: Free tier is fine for development

### 2.3 Set Environment Variables in Render Dashboard
Copy from `.env.render`:

```
DATABASE_URL=postgresql://neondb_owner:...
DB_SSLMODE=require
AUTH_REQUIRED=true
FIREBASE_SERVICE_ACCOUNT_JSON={...full JSON...}
CORS_ORIGINS=https://risk-atlas.vercel.app
CORS_ORIGIN_REGEX=^https?://(localhost|127\.0\.0\.1)(:\d+)?$|^https://.*\.vercel\.app$
MAX_DETECT_ROWS=50000
MAX_SHAP_EXPLANATIONS=40
```

### 2.4 Deploy
- Click "Deploy" → Wait 5-10 minutes
- Copy your service URL: `https://risk-atlas-api.onrender.com` (example)

✅ **Verify**: Open in browser:
```
https://your-render-service.onrender.com/health
```

**Expected Response**:
```json
{
  "status": "ok",
  "model": "loaded",
  "threshold": 0.5,
  "auth_required": true,
  "db_configured": true
}
```

---

## **STEP 3: Frontend Deployment - Vercel** 🌐

### 3.1 Connect Repository to Vercel
1. Go to [vercel.com](https://vercel.com)
2. Click "Add New" → "Project"
3. Import your GitHub repository
4. Select this repo

### 3.2 Configure Vercel Settings
- **Framework Preset**: Static Site (Other)
- **Root Directory**: `website`
- **Build Command**: `echo 'Vercel deployment ready'` (or leave blank)
- **Output Directory**: `.` (current directory)

### 3.3 Deploy
- Click "Deploy" → Wait 1-2 minutes
- Copy your site URL: `https://risk-atlas.vercel.app` (example)

✅ **Verify**: Open in browser:
```
https://your-vercel-site.vercel.app
```

**Expected**: Landing page loads with "Risk Atlas" branding

---

## **STEP 4: Connect Frontend to Backend** 🔗

Once both are deployed:

1. Open your Vercel frontend
2. Click sidebar → "API Settings"
3. Enter your Render backend URL:
   ```
   https://your-render-service.onrender.com
   ```
4. Save

Alternatively, backend URL is stored in browser localStorage as `apiBase`

---

## **STEP 5: Update CORS in Render** (if Vercel URL changes)

If you need to change your Vercel domain:

1. Go to Render service dashboard
2. Settings → Environment Variables
3. Update `CORS_ORIGINS` to your new Vercel URL
4. Reboot service

---

## **STEP 6: Smoke Tests** ✅

### Test Flow:
1. **Health Check**
   ```bash
   curl https://your-render-service.onrender.com/health
   ```

2. **Sign In** (on Vercel frontend)
   - Click "Sign Up"
   - Create account with email/password
   - You should see Firebase auth UI

3. **Upload Sample Data**
   - Download `sample_transactions.csv`
   - Click "Upload" on dashboard
   - Wait 10-30 seconds

4. **Check Results**
   - Should see fraud alerts
   - Click on alert for details
   - Check SHAP explanations

5. **Verify Database** (in Neon SQL Editor)
   ```sql
   SELECT COUNT(*) as transaction_count FROM transactions;
   SELECT COUNT(*) as alert_count FROM alerts WHERE severity = 'high';
   ```

---

## **TROUBLESHOOTING** 🔧

### "Connection refused" to database
- Check `DATABASE_URL` in Render env vars
- Verify Neon project exists and is running
- Test in Neon SQL Editor first

### "Auth token invalid"
- Check `FIREBASE_SERVICE_ACCOUNT_JSON` formatting
- Ensure it's a single-line JSON (no newlines in env var)
- Verify Firebase project ID matches

### "CORS error" in browser console
- Update `CORS_ORIGINS` in Render to match Vercel URL
- Include full HTTPS URL: `https://your-domain.vercel.app`

### Frontend blank/loading forever
- Check browser console for errors
- Verify `firebase-config.js` has values
- Check API Settings points to correct Render URL

### Model file not found
- Model `backend/fraud_model.pkl` must exist in repo
- Check file is committed to git
- Verify it's not in `.gitignore`

---

## **PRODUCTION BEST PRACTICES** 🛡️

### Environment Security
- ✅ Never commit `.env` to git
- ✅ Use Render Secrets Manager for sensitive data
- ✅ Rotate Firebase keys periodically
- ✅ Use Neon connection pooling

### Monitoring
- Check Render logs: Dashboard → Logs
- Monitor database size in Neon console
- Set up alerts for model threshold changes

### Scaling
- Render free tier: ~100 concurrent requests
- Neon free tier: 3GB storage
- Upgrade as needed

### Maintenance
- Update dependencies quarterly
- Retrain model with new fraud patterns
- Archive old alerts monthly

---

## **QUICK REFERENCE** 📋

| Component | Provider | Status | URL |
|-----------|----------|--------|-----|
| Backend API | Render | 🟢 Live | `https://risk-atlas-api.onrender.com` |
| Frontend | Vercel | 🟢 Live | `https://risk-atlas.vercel.app` |
| Database | Neon | 🟢 Live | Neon dashboard |
| Auth | Firebase | 🟢 Live | Firebase console |

---

## **SUPPORT** 💬

For issues, check:
1. Render logs (Backend)
2. Browser DevTools (Frontend)
3. Neon SQL Editor (Database)
4. Firebase Console (Auth)
5. `DSA_with_Python_Project_Documentation.txt`

---

**Deployed by**: Avishkaar Bhor  
**Last Updated**: March 7, 2026  
**Status**: ✅ Production Ready
