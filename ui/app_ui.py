"""
Gradio application entry point.
Mounts the Flask API and serves the React built dist folder.
"""

import os
from pathlib import Path
import gradio as gr
from werkzeug.middleware.dispatcher import DispatcherMiddleware

# Import the Flask app
from api.app import app as flask_app
from config.settings import settings

def build_gradio_app():
    """
    Builds the Gradio Blocks UI that embeds the Flask-served React application via an iframe.
    """
    with gr.Blocks(title="Personalized Reading Recommendation Agent", css="body {margin: 0; padding: 0; overflow-x: hidden;}") as demo:
        gr.HTML(
            f"""
            <iframe src="http://127.0.0.1:5000/" style="width: 100vw; height: 100vh; border: none; margin: 0; padding: 0; overflow: hidden;"></iframe>
            """
        )
        
    return demo
