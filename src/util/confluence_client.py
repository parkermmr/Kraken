"""
Handles API communication with Confluence.
"""

import requests
import re
from urllib.parse import urlparse


class ConfluenceClient:
    """Client to interact with Confluence REST API."""

    def __init__(self, base_url, username, token):
        self.base_url = base_url.rstrip("/")
        parsed = urlparse(self.base_url)
        self.domain = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        self.base_api_url = f"{self.domain}/rest/api/content"
        self.session = requests.Session()
        self.session.auth = (username, token)

    def get_page(self, page_id):
        """Retrieve a Confluence page by its ID."""
        url = f"{self.base_api_url}/{page_id}?expand=body.storage"
        resp = self.session.get(url)
        resp.raise_for_status()
        return resp.json()

    def get_children(self, page_id):
        """Retrieve immediate child pages for a given page."""
        url = f"{self.base_api_url}/{page_id}/child/page"
        resp = self.session.get(url)
        resp.raise_for_status()
        return resp.json().get("results", [])

    def get_images(self, page_id):
        """Retrieve images attached to a page."""
        url = f"{self.base_api_url}/{page_id}/child/attachment"
        resp = self.session.get(url)
        resp.raise_for_status()
        images = []
        for att in resp.json().get("results", []):
            media_type = att["metadata"].get("mediaType", "")
            if "image" in media_type:
                filename = att["title"]
                relative_url = att["_links"]["download"]
                if relative_url.startswith("/"):
                    full_url = self.domain + relative_url
                else:
                    full_url = relative_url
                images.append({"filename": filename, "url": full_url})
        return images

    def extract_page_id(self, page_url):
        """Extract the numeric page ID from a Confluence URL."""
        match = re.search(r"/pages/(\d+)", page_url)
        if match:
            return match.group(1)
        raise ValueError("Invalid Confluence URL format.")
