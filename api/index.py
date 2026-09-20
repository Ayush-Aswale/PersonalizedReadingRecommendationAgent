"""
Legacy Vercel entrypoint (kept for backward compatibility).
The primary entrypoint is now configured via pyproject.toml:
  [tool.vercel]
  entrypoint = "api.app:app"
"""

from api.app import app
