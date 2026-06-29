# MindWell v4.0 — Mental Health AI Platform

Google Gemini · 16 Psychological Conditions · Single Python File · Vercel Ready

## What's included
- Role-based onboarding (Patient / Doctor) — no API key prompt for users
- 16 conditions: Anxiety, Depression, OCD, PTSD, Bipolar, Panic, Social Anxiety,
  Eating Disorder, ADHD, Grief, Burnout, Sleep, Addiction, BPD, Schizophrenia, Phobia
- Automatic condition detection from conversation
- Voice input (Web Speech API)
- Mood tracker + session history
- Real-time biomarker panel (stress, energy, speech pace)
- Doctor dashboard + PHQ-9 + AI session summary
- Crisis detection → helplines shown immediately
- Multilingual: EN / Hindi / Marathi / Tamil
- Works in demo mode without any API key

## Run locally
```bash
pip install google-generativeai
export GOOGLE_API_KEY=AIza...   # Mac/Linux
set GOOGLE_API_KEY=AIza...      # Windows
python api/index.py
# Open http://localhost:3000
```

## Deploy to Vercel
1. Push this repo to GitHub
2. Go to vercel.com/new → import repo
3. Settings → Environment Variables → add GOOGLE_API_KEY
4. Deploy — live in 60 seconds

## API Endpoints
| Method | Path | Description |
|--------|------|-------------|
| GET | / | Full frontend app |
| POST | /api/chat | AI conversation + biomarkers |
| POST | /api/summary | Clinical session summary |
| POST | /api/mood | Log mood entry |
| GET | /api/conditions | All 16 conditions data |
| GET | /api/health | Health check |
