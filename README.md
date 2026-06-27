# MindWell v3.0 — Deployment Guide

## Files in this repo
```
api/index.py      ← entire app (single file)
vercel.json       ← Vercel routing config
requirements.txt  ← only google-generativeai needed
```

## Deploy to Vercel (3 steps)

1. **Push these 3 files to your GitHub repo**
   - Replace the old `api/index.py` with this new one
   - Replace `vercel.json` and `requirements.txt`
   - Commit and push

2. **In Vercel dashboard → Settings → Environment Variables**
   - Add: `GOOGLE_API_KEY` = your Gemini API key
   - (Optional) `JWT_SECRET` = any random string

3. **Redeploy** — Vercel picks up the new files automatically

## Run locally
```bash
pip install google-generativeai
export GOOGLE_API_KEY=AIza...
python api/index.py
# Open http://localhost:3000
```

## What's fixed in v3.0
- ✅ Proper onboarding modal — asks Patient vs Doctor first
- ✅ API key step with clear instructions
- ✅ Quick-start condition chips in onboarding
- ✅ Doctor flow goes straight to Clinical Dashboard
- ✅ AI chat actually works (fixed status code bug)
- ✅ Session history saves automatically
- ✅ Generate AI Summary button in Doctor view
- ✅ Bio panel shows dashes until first message (not fake values)
- ✅ All HTTP status codes correct (was hardcoded "OK" before)
- ✅ user_type passed to Gemini for clinical vs patient language
