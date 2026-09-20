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
    """
    WSGI Middleware to fix routing on Vercel.
    Vercel's Python runtime can sometimes overwrite PATH_INFO with the rewrite destination 
    (e.g. /api/index.py) or strip the /api prefix. This explicitly restores the true PATH_INFO 
    from the original request URI.
    """
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        # Prefer the original requested URI if available from standard WSGI/Vercel headers
        req_uri = environ.get("REQUEST_URI") or environ.get("RAW_URI") or environ.get("HTTP_X_NOW_ROUTE_MATCHES")
        if req_uri:
            # Strip query string for PATH_INFO
            path = req_uri.split("?")[0]
            environ["PATH_INFO"] = path
        else:
            # Fallback for environments that just strip the /api prefix
            path = environ.get("PATH_INFO", "")
            if not path.startswith("/api"):
                environ["PATH_INFO"] = "/api" + path
                
        return self.wsgi_app(environ, start_response)


# Vercel looks for the `app` variable
app = VercelPathFix(flask_app)
