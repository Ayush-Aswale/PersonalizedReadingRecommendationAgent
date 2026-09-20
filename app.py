"""
Main entry point for local development.
Combines Gradio and the Flask API into a single server using WSGI middleware.
"""

import sys
import threading
from pathlib import Path
from werkzeug.serving import make_server

# Add current directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from api.app import app as flask_app
from ui.app_ui import build_gradio_app

class ServerThread(threading.Thread):
    def __init__(self, app, port):
        threading.Thread.__init__(self)
        self.server = make_server('127.0.0.1', port, app)
        self.ctx = app.app_context()
        self.ctx.push()

    def run(self):
        print("Starting Flask API on port 5000...")
        self.server.serve_forever()

    def shutdown(self):
        self.server.shutdown()

if __name__ == "__main__":
    # Check if database is built
    from config.settings import settings
    if not settings.sqlite_path.exists():
        print("Database not found. Running ingestion script...")
        from data.ingest import ingest_data
        try:
            ingest_data()
        except Exception as e:
            print(f"Error during ingestion: {e}")
            print("Please run `python scripts/generate_books.py` first.")
            sys.exit(1)

    # 1. Start Flask API on a background thread (port 5000)
    # The React app will hit http://127.0.0.1:5000/api/...
    flask_thread = ServerThread(flask_app, 5000)
    flask_thread.start()
    
    # 2. Start Gradio UI (port 7860)
    try:
        demo = build_gradio_app()
        demo.launch(server_name="127.0.0.1", server_port=7860, show_error=True)
    finally:
        flask_thread.shutdown()
