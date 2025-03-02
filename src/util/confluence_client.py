"""
Handles API communication with Confluence, including support for both
numeric page URLs ("/pages/12345") and space/title URLs ("/display/SPACE/TITLE").
"""


import re
import requests
from urllib.parse import urlparse, quote


class ConfluenceClient:
    """
    Client to interact with the Confluence REST API.
    """

    def __init__(self, base_url: str, username: str, token: str) -> None:
        """
        Initialize the ConfluenceClient with a base URL, username, and token.
        """
        self.base_url: str = base_url.rstrip("/")
        parsed = urlparse(self.base_url)
        self.domain: str = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        self.base_api_url: str = f"{self.domain}/rest/api/content"
        self.session: requests.Session = requests.Session()
        self.session.auth = (username, token)

    def get_page(self, page_id: str) -> dict:
        """
        Retrieve a Confluence page by ID, returning JSON data.
        """
        url: str = f"{self.base_api_url}/{page_id}?expand=body.storage"
        resp: requests.Response = self.session.get(url)
        resp.raise_for_status()
        return resp.json()

    def get_children(self, page_id: str) -> list:
        """
        Retrieve immediate child pages for a given page.
        Returns a list of page objects.
        """
        url: str = f"{self.base_api_url}/{page_id}/child/page"
        resp: requests.Response = self.session.get(url)
        resp.raise_for_status()
        return resp.json().get("results", [])

    def get_images(self, page_id: str) -> list:
        """
        Retrieve images attached to a page.
        Returns a list of dicts with 'filename' and 'url' keys.
        """
        url: str = f"{self.base_api_url}/{page_id}/child/attachment"
        resp: requests.Response = self.session.get(url)
        resp.raise_for_status()

        images: list = []
        data: dict = resp.json()
        for att in data.get("results", []):
            media_type: str = att["metadata"].get("mediaType", "")
            if "image" in media_type:
                fn: str = att["title"]
                rel: str = att["_links"]["download"]
                full_url: str = self.domain + rel if rel.startswith("/") else rel
                images.append({"filename": fn, "url": full_url})
        return images

    def extract_page_id(self, page_url: str) -> str:
        """
        Extract the numeric ID from a Confluence URL of the form
        '/pages/12345', or else parse '/display/SPACE/TITLE' and
        look up the numeric ID from space + title.
        """
        numeric: re.Match = re.search(r"/pages/(\d+)", page_url)
        if numeric:
            return numeric.group(1)

        space_title: re.Match = re.search(r"/display/([^/]+)/([^/]+)$", page_url)
        if space_title:
            space_key: str = space_title.group(1)
            page_title: str = space_title.group(2)
            return self.get_page_id_by_space_title(space_key, page_title)

        raise ValueError(f"Invalid Confluence URL format: {page_url}")

    def get_page_id_by_space_title(self, space_key: str, page_title: str) -> str:
        """
        Look up a page's numeric ID by space key and page title.
        """
        safe_space: str = quote(space_key, safe="")
        safe_title: str = quote(page_title, safe="")
        url: str = (
            f"{self.base_api_url}"
            f"?spaceKey={safe_space}"
            f"&title={safe_title}"
            f"&limit=1"
        )
        resp: requests.Response = self.session.get(url)
        resp.raise_for_status()
        data: dict = resp.json()
        results: list = data.get("results", [])
        if not results:
            msg: str = (
                f"No page found for space '{space_key}' "
                f"and title '{page_title}'."
            )
            raise ValueError(msg)
        return results[0]["id"]
