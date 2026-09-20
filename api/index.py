"""
Vercel Serverless Entrypoint.
This file exposes the Flask application to Vercel's Python runtime.

Vercel's Python runtime strips the /api prefix from PATH_INFO when routing
to files inside the api/ directory. Since all Flask routes are defined with
the /api/ prefix (e.g. /api/users), we use a thin WSGI middleware to
restore the prefix so Flask's routing matches correctly.

Database seeding must be performed via a one-time deployment script
(e.g., running `python data/ingest.py` locally while pointing DATABASE_URL to production).
"""

from api.app import app as flask_app


class VercelPathFix:
    """WSGI middleware that restores the /api prefix stripped by Vercel's runtime."""

    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        path = environ.get("PATH_INFO", "")
        if not path.startswith("/api"):
            environ["PATH_INFO"] = "/api" + path
        return self.wsgi_app(environ, start_response)


# Vercel looks for the `app` variable
app = VercelPathFix(flask_app)
