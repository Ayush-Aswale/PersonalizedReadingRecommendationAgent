"""
Vercel Serverless Entrypoint — Diagnostic version.
Reports the actual import error as JSON instead of a generic 500.
"""

import sys
import os
import traceback

# Diagnostic: try to import the real Flask app, catch and report errors
_import_error = None
_flask_app = None

try:
    from api.app import app as _flask_app
except Exception as e:
    _import_error = traceback.format_exc()
    # Try alternative import path
    try:
        from app import app as _flask_app
    except Exception as e2:
        _import_error += "\n\n--- Alternative import also failed ---\n"
        _import_error += traceback.format_exc()

if _flask_app is not None:
    app = _flask_app
else:
    # Create a minimal Flask app that reports the error
    from flask import Flask, jsonify
    app = Flask(__name__)

    @app.route("/api/debug")
    def debug():
        return jsonify({
            "error": "Flask app failed to import",
            "traceback": _import_error,
            "sys_path": sys.path,
            "cwd": os.getcwd(),
            "dir_listing": os.listdir(os.getcwd()) if os.path.isdir(os.getcwd()) else "N/A",
            "api_dir": os.listdir(os.path.join(os.getcwd(), "api")) if os.path.isdir(os.path.join(os.getcwd(), "api")) else "N/A",
            "env_keys": [k for k in os.environ.keys() if not k.startswith("_")],
        })

    @app.route("/api/users")
    def users_fallback():
        return jsonify({
            "error": "Flask app failed to import",
            "traceback": _import_error,
        }), 500
