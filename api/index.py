"""
Vercel Serverless Entrypoint.
This file exposes the Flask application to Vercel's Python runtime.
It intentionally does not perform database schema initialization or CSV ingestion 
on cold-starts to prevent concurrent execution conflicts and timeout risks.

Database seeding must be performed via a one-time deployment script 
(e.g., running `python data/ingest.py` locally while pointing DATABASE_URL to production).
"""

from api.app import app

# Vercel's Python runtime automatically looks for the `app` variable in `api/index.py`.
