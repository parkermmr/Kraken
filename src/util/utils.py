"""
Utility functions.
"""

import re


def sanitize_title(title):
    """Convert a page title into a safe filename."""
    title = title.strip().replace(" ", "_")
    return re.sub(r"[^\w\-\.]", "", title)


def replace_blob_image_refs(markdown, images):
    """
    Replace markdown image references with blob URLs with local references.

    For each image in images, if a markdown image reference contains a blob:
    URL and its alt text (or part of it) matches the image filename, replace the
    URL with "images/<filename>".
    """
    for img in images:
        pattern = re.compile(
            r'(!\[[^\]]*' + re.escape(img["filename"]) +
            r'[^\]]*\]\()blob:[^)]+\)'
        )
        markdown = pattern.sub(r'\1images/' + img["filename"] + ')', markdown)
    return markdown
