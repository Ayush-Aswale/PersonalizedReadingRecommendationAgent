"""
Flask API layer for the recommendation agent.
This is the same file used by Vercel serverless and mounted locally by Gradio.
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

from agent.orchestrator import run_turn
from database import db
from utils.validators import sanitize_text

import os
from config.settings import settings

dist_dir = str(settings.PROJECT_ROOT / "frontend" / "dist")
_dist_exists = os.path.isdir(dist_dir)
# Do NOT set static_folder — Flask's built-in static handler would intercept SPA routes
# before our catch-all can do the React Router fallback. We handle static serving manually.
app = Flask(__name__)
CORS(app) # Allow cross-origin requests if needed for separated frontends

@app.route("/")
def index():
    if _dist_exists:
        return send_from_directory(dist_dir, "index.html")
    return jsonify({"status": "API is running", "frontend": "not built"}), 200

# Serve other static files (like /assets/*) and SPA fallback
@app.route("/<path:path>")
def serve_static(path):
    # API routes that didn't match a defined endpoint should 404, not serve index.html
    if path.startswith("api/"):
        return jsonify({"error": "not found"}), 404
    if _dist_exists:
        file_path = os.path.join(dist_dir, path)
        if os.path.isfile(file_path):
            return send_from_directory(dist_dir, path)
        # SPA fallback: return index.html for React Router client-side routes
        return send_from_directory(dist_dir, "index.html")
    return jsonify({"error": "not found"}), 404

# ── Users ────────────────────────────────────────────────────────────────

@app.route('/api/users', methods=['GET'])
def list_users():
    """Returns all registered users with their display names."""
    with db.get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, display_name, created_at FROM users ORDER BY created_at DESC")
        users = [dict(row) for row in cursor.fetchall()]
    return jsonify(users)

@app.route('/api/users', methods=['POST'])
def create_user():
    """Creates a new user and their initial preferences in a single call."""
    data = request.json or {}
    display_name = data.get("display_name", "").strip()
    if not display_name:
        return jsonify({"error": "display_name is required"}), 400
    
    # Generate a slug-based user_id from display name
    import re, uuid
    slug = re.sub(r'[^a-z0-9]+', '_', display_name.lower()).strip('_')
    user_id = f"{slug}_{uuid.uuid4().hex[:6]}"
    
    try:
        with db.get_db_connection() as conn:
            cursor = conn.cursor()
            # Insert user
            cursor.execute(
                f"INSERT INTO users (user_id, display_name) VALUES ({db._param('uid')}, {db._param('name')})",
                {"uid": user_id, "name": display_name}
            )
            # Insert preferences
            cursor.execute(f"""
                INSERT INTO preferences (user_id, favorite_genres, favorite_authors, reading_level, preferred_length, current_mood)
                VALUES ({db._param('uid')}, {db._param('genres')}, {db._param('authors')}, {db._param('level')}, {db._param('length')}, {db._param('mood')})
            """, {
                "uid": user_id,
                "genres": data.get("favorite_genres", ""),
                "authors": data.get("favorite_authors", ""),
                "level": data.get("reading_level", "medium"),
                "length": data.get("preferred_length", "medium"),
                "mood": data.get("current_mood", ""),
            })
            conn.commit()
        
        return jsonify({"success": True, "user_id": user_id, "display_name": display_name}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# ── Chat & Agent ────────────────────────────────────────────────────────

@app.route('/api/chat', methods=['POST'])
def chat():
    """Main conversational endpoint. Triggers the LangChain agent."""
    data = request.json or {}
    user_id = data.get("user_id")
    message = data.get("message")
    
    if not user_id or not message:
        return jsonify({"error": "user_id and message are required"}), 400
        
    message = sanitize_text(message)
    result = run_turn(user_id, message)
    
    return jsonify(result)

# ── User Profile ────────────────────────────────────────────────────────

@app.route('/api/profile/<user_id>', methods=['GET'])
def get_profile(user_id):
    profile = db.get_user_profile(user_id)
    return jsonify(profile)

@app.route('/api/profile/<user_id>', methods=['PUT'])
def update_profile(user_id):
    data = request.json or {}
    try:
        for field, value in data.items():
            if field != "user_id":
                db.update_user_preference(user_id, field, str(value))
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# ── History & Favorites ──────────────────────────────────────────────────

@app.route('/api/history/<user_id>', methods=['GET'])
def get_history(user_id):
    history = db.get_reading_history(user_id)
    return jsonify(history)

@app.route('/api/favorites/<user_id>', methods=['GET'])
def get_favorites(user_id):
    with db.get_db_connection() as conn:
        cursor = conn.cursor()
        # Dialect specific params
        param = "%(uid)s" if getattr(db.settings, 'is_production', False) else ":uid"
        cursor.execute(f"SELECT b.* FROM favorites f JOIN books b ON f.book_id = b.book_id WHERE f.user_id = {param}", {"uid": user_id})
        favorites = [dict(row) for row in cursor.fetchall()]
    return jsonify(favorites)

@app.route('/api/favorites', methods=['POST'])
def add_favorite():
    data = request.json or {}
    user_id = data.get("user_id")
    book_id = data.get("book_id")
    if not user_id or not book_id:
        return jsonify({"error": "user_id and book_id required"}), 400
    db.add_to_favorites(user_id, book_id)
    return jsonify({"success": True})

@app.route('/api/feedback', methods=['POST'])
def add_feedback():
    data = request.json or {}
    user_id = data.get("user_id")
    book_id = data.get("book_id")
    sentiment = data.get("sentiment")
    if not user_id or not book_id or sentiment not in ["like", "dislike"]:
        return jsonify({"error": "invalid request"}), 400
    db.record_feedback(user_id, book_id, sentiment, data.get("reason"))
    return jsonify({"success": True})

@app.route('/api/mark-read', methods=['POST'])
def mark_read():
    data = request.json or {}
    user_id = data.get("user_id")
    book_id = data.get("book_id")
    if not user_id or not book_id:
        return jsonify({"error": "invalid request"}), 400
    db.mark_as_read(user_id, book_id, data.get("rating"))
    return jsonify({"success": True})

# ── Books ───────────────────────────────────────────────────────────────

@app.route('/api/books/<book_id>', methods=['GET'])
def get_book(book_id):
    book = db.get_book_details(book_id)
    if book:
        return jsonify(book)
    return jsonify({"error": "not found"}), 404

# Export the app for Vercel
application = app

if __name__ == "__main__":
    app.run(debug=True, port=8000)
