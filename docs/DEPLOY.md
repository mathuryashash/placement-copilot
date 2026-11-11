# Deploy Guide

This project is NOT deployed. These are the steps to deploy it when ready.

## Prerequisites

- A free [Render](https://render.com) account for the backend
- A free [Vercel](https://vercel.com) account for the frontend
- API keys for Groq and/or Gemini (free tier)

## Backend (Render)

1. Fork or push this repo to GitHub.
2. In Render dashboard, click "New" → "Blueprint" and select this repo.
3. Render reads `render.yaml` and creates a web service + Postgres database.
4. **Manual step:** Render's managed Postgres does not enable the `vector` extension automatically.
   Connect to the DB (Render provides a "Connect" button) and run:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   CREATE EXTENSION IF NOT EXISTS pg_trgm;
   ```
5. Set environment variables in the Render dashboard:
   - `GROQ_API_KEY` — your Groq key
   - `GEMINI_API_KEY` — your Gemini key (optional fallback)
   - `CORS_ORIGINS` — your Vercel frontend URL
6. Deploy and wait for health check to pass at `/health`.

## Frontend (Vercel)

1. In Vercel, import the GitHub repo and set root directory to `frontend`.
2. Add environment variable: `NEXT_PUBLIC_API_URL` = your Render backend URL.
3. Deploy.

## Seed the corpus

After both services are live:
```bash
cd data/synthetic
python generator.py          # generates notices in data/synthetic/notices/
# Then use the ingest API to upload each notice:
for f in data/synthetic/notices/*.txt; do
  curl -X POST https://<your-backend>.onrender.com/api/v1/ingest/text \
    -H 'Content-Type: application/json' \
    -d "{\"text\": \"$(cat $f | sed 's/"/\\"/g')\"}"
done
```

## Vercel frontend notes

Vercel automatically handles:
- HTTPS/TLS termination
- Edge CDN for static assets
- Preview deployments for PRs

The frontend is a Next.js App Router app; no special Vercel config needed.
