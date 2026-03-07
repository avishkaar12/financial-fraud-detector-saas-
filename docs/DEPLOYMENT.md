# Deployment Guide (Vercel + Render + Neon + Firebase)

This repo deploys as:
- Website on Vercel from `website/`
- FastAPI backend on Render from `backend/`
- PostgreSQL on Neon
- Authentication on Firebase

## Neon (Database)
1. Create a Neon project and copy the pooled connection URI.
2. In Neon SQL Editor, run schema setup for:
   - `transactions`
   - `model_logs`
   - `alerts`
3. Keep SSL required (`sslmode=require`).

## Firebase (Auth)
1. Create Firebase project.
2. Enable Authentication providers (Email/Password and optionally Google).
3. Create Web app and collect config keys.
4. Generate service account JSON for backend token verification.

## Render (Backend API)
1. Create Render Web Service from this repo.
2. Build command:
   - `pip install -r backend/requirements.txt`
3. Start command:
   - `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
4. Environment variables:
   - `DATABASE_URL` = Neon connection URI
   - `DB_SSLMODE` = `require`
   - `AUTH_REQUIRED` = `true`
   - `FIREBASE_SERVICE_ACCOUNT_JSON` = one-line JSON
   - `CORS_ORIGINS` = Vercel production URL (comma-separated if multiple)
   - Optional: `CORS_ORIGIN_REGEX` = `https://.*\\.vercel\\.app`

After deploy, copy backend URL, for example:
- `https://risk-atlas-api.onrender.com`

## Vercel (Website)
1. Create a new Vercel project and import this repo.
2. Set Root Directory to `website`.
3. Framework preset: Other.
4. Build command: none.
5. Output directory: `.`
6. Copy `website/firebase-config.example.js` to `website/firebase-config.js`.
7. Set `website/firebase-config.js` values before production deploy.

After deploy, copy website URL, for example:
- `https://risk-atlas-portal.vercel.app`

## Connect Website -> API
- Open the deployed website.
- In left sidebar "API Settings", set API Base to Render URL.
- Sign in with Firebase on the website.
- Website sends Firebase token via `Authorization: Bearer <token>`.

## Smoke Checklist
1. Backend: open `https://your-service.onrender.com/health`
2. Website: open `https://your-project.vercel.app`
3. Set API Base to Render URL in website UI.
4. Sign in on website.
5. Upload `sample_transactions.csv`.
6. Verify rows in Neon:
   - `transactions`
   - `model_logs`
   - `alerts`
