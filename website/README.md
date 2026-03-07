# Website (React)

This is a React-based website (no build step required).

## Run Locally
1. Start backend:

```bash
uvicorn backend.main:app --reload
```

2. Start website server:

```bash
python -m http.server 5500
```

Open:
- `http://127.0.0.1:5500/website/`

Before running auth locally:
- Create `website/firebase-config.js` from `website/firebase-config.example.js`
- Fill your Firebase Web App config values.

## Production
- Deploy `website/` to Vercel (Root Directory: `website`).
- Deploy backend to Render.
- Include a production `firebase-config.js` with your Firebase Web App config.
- In the website, set API Base to your Render URL.
