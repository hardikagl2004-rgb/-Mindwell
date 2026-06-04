# MindWell — Vercel Deployment Guide

Single Python file, zero build step, live in 3 minutes.

---

## Files

```
mindwell-vercel/
├── api/
│   └── index.py        ← entire app (frontend + backend in one file)
├── requirements.txt    ← anthropic, pyjwt, jinja2
├── vercel.json         ← routing config
└── README.md
```

---

## Deploy to Vercel (3 steps)

### Step 1 — Push to GitHub
```bash
git init
git add .
git commit -m "MindWell v1"
git remote add origin https://github.com/YOUR_USERNAME/mindwell.git
git push -u origin main
```

### Step 2 — Import on Vercel
1. Go to https://vercel.com/new
2. Click "Import Git Repository"
3. Select your mindwell repo
4. Click "Deploy" (Vercel auto-detects Python)

### Step 3 — Add API Key
1. In your Vercel project → Settings → Environment Variables
2. Add: `ANTHROPIC_API_KEY` = `sk-ant-...`
3. Redeploy (Settings → Deployments → Redeploy)

Your app is live at: `https://mindwell-xxx.vercel.app`

---

## Run Locally

```bash
pip install anthropic pyjwt jinja2
export ANTHROPIC_API_KEY=sk-ant-...
python api/index.py
# Open http://localhost:3000
```

---

## API Endpoints

All routes handled in `api/index.py`:

| Method | Path                  | Description                        |
|--------|-----------------------|------------------------------------|
| GET    | /                     | Frontend app (full HTML)           |
| POST   | /api/chat             | AI conversation + biomarkers       |
| POST   | /api/mood             | Log mood entry                     |
| GET    | /api/mood/trend       | 14-day mood trend data             |
| POST   | /api/auth/send-otp    | Send OTP to phone                  |
| POST   | /api/auth/verify-otp  | Verify OTP, get JWT                |
| POST   | /api/summary          | Generate clinical session summary  |
| POST   | /api/alert            | Log a crisis alert                 |
| GET    | /api/health           | Health check + status              |

---

## Chat API Example

```bash
curl -X POST https://your-app.vercel.app/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I have been feeling very anxious lately",
    "history": [],
    "language": "en",
    "mood": "Anxious"
  }'
```

Response:
```json
{
  "reply": "That anxious feeling can be so consuming...",
  "biomarkers": {
    "stress": 6.5,
    "energy": 0.78,
    "pace": 158,
    "emotion": "anxious",
    "insight": "Anxiety presentation detected.",
    "psycho": "The 4-7-8 breath reverses cortisol response in 60 seconds.",
    "crisis": false
  },
  "crisis": false
}
```

---

## Notes for Production

- **Database**: Replace in-memory dicts with Vercel KV (Redis) or Supabase (Postgres)
- **SMS**: Add Twilio credentials to env vars for real crisis SMS alerts
- **Auth**: OTP_STORE resets on cold start — move to Redis for persistence
- **Voice biomarker model**: Runs as a separate service (too large for Vercel serverless)
- **DPDP compliance**: Add consent banner and data deletion endpoint before going live in India

---

## Environment Variables

| Variable          | Required | Description                    |
|-------------------|----------|--------------------------------|
| ANTHROPIC_API_KEY | Yes      | Your Claude API key            |
| JWT_SECRET        | No       | Custom JWT secret (recommended)|
