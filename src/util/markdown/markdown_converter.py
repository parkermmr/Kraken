"""
Custom Markdown Converter using built-in HTMLParser.

This module processes raw Confluence HTML without external libraries.
Confluence stores images inside <ac:image> tags containing <ri:attachment>
children. This parser logs every tag encountered and replaces each
ac:image block (and standard <img> tags) with an inline Markdown image
reference. The alt text is preserved, while the image filename (used in the
link) is sanitized (e.g. spaces become underscores).
"""

import logging
from src.util.markdown.markdown_parser import MarkdownParser

logger = logging.getLogger(__name__)


class MarkdownConverter:
    def __init__(self, client):
        self.client = client

    def convert(self, html_content: str) -> str:
        logger.info("Starting custom Markdown conversion.")
        logger.debug("Raw HTML snippet (first 500 chars): %s", html_content[:500])
        parser = MarkdownParser(self.client)
        parser.feed(html_content)
        markdown = parser.get_markdown()
        logger.info("Markdown conversion complete; output length: %d", len(markdown))
        return markdown
