"""
Utility functions.
"""

import re


def sanitize_title(title):
    """
    Convert a page title into a safe filename
    while keeping recognizable characters.
    """
    title = title.strip()
    title = title.replace("/", "-").replace("\\", "-")
    return re.sub(r'[<>:"|?*]', "", title)


def replace_blob_image_refs(markdown, images):
    """
    Replace markdown image references with blob URLs with local references.

    For each image in images, if a markdown image reference contains a blob:
    URL and its alt text (or part of it) matches the image filename, replace the
    URL with "images/<filename>".
    """
    for img in images:
        pattern = re.compile(
            r"(!\[[^\]]*" + re.escape(img["filename"]) + r"[^\]]*\]\()blob:[^)]+\)"
        )
        markdown = pattern.sub(r"\1images/" + img["filename"] + ")", markdown)
    return markdown


def decode_literal_unicode_escapes(text: str) -> str:
    """
    Decode literal backslash-escaped Unicode sequences like \\uXXXX or
    \\UXXXXXXXX, preserving normal emoji codepoints and other characters.
    """
    pattern: re.Pattern = re.compile(r"(\\u[0-9A-Fa-f]{4}|\\U[0-9A-Fa-f]{8})+")

    def decode_match(match: re.Match) -> str:
        raw: str = match.group(0)
        try:
            return raw.encode("ascii", errors="ignore").decode(
                "unicode_escape", errors="ignore"
            )
        except UnicodeDecodeError:
            return raw

    return pattern.sub(decode_match, text)
