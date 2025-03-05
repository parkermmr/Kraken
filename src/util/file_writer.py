"""
Handles writing Markdown and image files.
"""

import os

import requests

from src.util.logging.logger import Logger

logger = Logger(__name__, level=20, colored=False)


class FileWriter:
    """Handles file writing and saving assets."""

    def save_markdown_file(self, file_path, content):
        """Save Markdown content to a specific file path."""
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8", errors="ignore") as f:
            f.write(content)
        logger.info("Saved file: %s", file_path)

    def save_image(self, output_dir, filename, url, session=None):
        """Download and save an image using the provided session."""
        if session is None:
            session = requests
        response = session.get(url, stream=True)
        response.raise_for_status()
        file_path = os.path.join(output_dir, "images", filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "wb") as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
        logger.info("Saved image: %s", file_path)
