# MindWell v4.0 — Mental Health AI Platform

Google Gemini · 16 Psychological Conditions · No API key prompt for users

## File structure (IMPORTANT — must be exactly this)
```
-Mindwell/
├── api/
│   └── index.py      ← ONLY file here
├── vercel.json
├── requirements.txt
├── .gitignore
└── README.md
```

## Deploy
1. Make sure GOOGLE_API_KEY is set in Vercel → Settings → Environment Variables
2. Push this repo → Vercel auto-deploys

## Run locally
```
pip install google-generativeai
export GOOGLE_API_KEY=AIza...
python api/index.py
```
