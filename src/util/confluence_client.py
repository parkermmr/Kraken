"""
Handles API communication with Confluence, including support for both
numeric page URLs ("/pages/12345"), space/title URLs ("/display/SPACE/TITLE"),
and space-only URLs ("/spaces/SPACE" or "/display/SPACE").
"""

import re
from urllib.parse import quote, urlparse

import requests


class ConfluenceClient:
    """
    Client to interact with Confluence's REST API.
    """

    def __init__(self, base_url: str, username: str, token: str) -> None:
        """
        Initialize the ConfluenceClient with a base URL, username, and token.
        """
        self.base_url: str = base_url.rstrip("/")
        parsed = urlparse(self.base_url)
        self.domain: str = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        self.base_api_url: str = f"{self.domain}/rest/api/content"
        self.space_api_url: str = f"{self.domain}/rest/api/space"
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
        for att in resp.json().get("results", []):
            meta: dict = att.get("metadata", {})
            media_type: str = meta.get("mediaType", "")
            if "image" in media_type:
                fn: str = att["title"]
                rel: str = att["_links"]["download"]
                full_url: str = self.domain + rel if rel.startswith("/") else rel
                images.append({"filename": fn, "url": full_url})
        return images

    def extract_page_id(self, page_url: str) -> str:
        """
        Extract the numeric ID from a Confluence URL.
        1) If it matches '/pages/(\\d+)', return the numeric ID.
        2) Else if it matches '/display/SPACE/TITLE', look up numeric ID from space.
        3) Else if it matches '/spaces/SPACE' or '/display/SPACE',
           fetch the default homepage ID for that space.
        """
        numeric: re.Match = re.search(r"/pages/(\d+)", page_url)
        if numeric:
            return numeric.group(1)

        space_title: re.Match = re.search(
            r"/(?:display|spaces)/([^/]+)/([^/]+)$", page_url
        )
        if space_title:
            space_key: str = space_title.group(1)
            page_title: str = space_title.group(2)
            return self.get_page_id_by_space_title(space_key, page_title)

        space_only: re.Match = re.search(r"/(?:display|spaces)/([^/]+)/?$", page_url)
        if space_only:
            space_key_only: str = space_only.group(1)
            return self.get_space_homepage_id(space_key_only)

        raise ValueError(f"Unrecognized Confluence URL format: {page_url}")

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
                f"No page found for space '{space_key}' " f"and title '{page_title}'."
            )
            raise ValueError(msg)
        return results[0]["id"]

    def get_space_homepage_id(self, space_key: str) -> str:
        """
        Retrieve the homepage ID of a space (its default page).
        If the space doesn't exist or no homepage is found, raise ValueError.
        """
        safe_space: str = quote(space_key, safe="")
        url: str = f"{self.space_api_url}/{safe_space}?expand=homepage"
        resp: requests.Response = self.session.get(url)
        resp.raise_for_status()
        data: dict = resp.json()
        homepage: dict = data.get("homepage")
        if not homepage or "id" not in homepage:
            raise ValueError(
                f"Space '{space_key}' has no homepage or isn't accessible."
            )
        return homepage["id"]
