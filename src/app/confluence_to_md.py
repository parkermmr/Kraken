"""
Confluence to Markdown

This application converts Confluence pages into Markdown files,
building a hierarchical directory structure. It also transforms blob:
image URLs into download URLs so that images are downloaded properly.

Usage:
"""

import os
from src.app.config import parse_args
from src.util.confluence_client import ConfluenceClient
from src.util.file_writer import FileWriter
from src.util.markdown.markdown_converter import MarkdownConverter
from src.util.logging.logging_config import setup_logging
from src.util.logging.logger import Logger
from src.util.utils import sanitize_title

setup_logging()
logger = Logger(__name__, level=20, colored=False)


def process_page(client, writer, converter, page_id, parent_dir, is_root=False):
    """
    Process a Confluence page: fetch content, write raw HTML for debugging,
    convert to Markdown, update inline image references, save the file, download
    images, and process child pages recursively.
    """
    try:
        page = client.get_page(page_id)
    except Exception as exc:
        logger.error("Error retrieving page %s: %s", page_id, exc,
                     extra={"caller": __name__})
        return

    title = page.get("title", f"page_{page_id}")
    children = client.get_children(page_id)
    safe_title = sanitize_title(title)
    if is_root:
        output_dir = parent_dir
        file_name = "index.md"
    else:
        if children:
            output_dir = os.path.join(parent_dir, safe_title)
            file_name = "index.md"
        else:
            output_dir = parent_dir
            file_name = f"{safe_title}.md"
    os.makedirs(output_dir, exist_ok=True)

    html_content = page["body"]["storage"]["value"]
    raw_html_file = os.path.join(output_dir, "raw.html")
    with open(raw_html_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    logger.info("Wrote raw HTML source to %s", raw_html_file)

    markdown_content = converter.convert(html_content)
    logger.debug("Markdown snippet (first 500 chars): %s", markdown_content[:500])
    content = f"# {title}\n\n{markdown_content}"
    writer.save_markdown_file(os.path.join(output_dir, file_name), content)

    images = client.get_images(page_id)
    for img in images:
        try:
            sanitized_name = sanitize_title(img["filename"])
            writer.save_image(output_dir, sanitized_name, img["url"],
                              session=client.session)
        except Exception as exc:
            logger.error("Error saving image %s: %s", img["filename"], exc,
                         extra={"caller": __name__})
    for child in children:
        process_page(client, writer, converter, child["id"], output_dir,
                     is_root=False)


class ConfluenceApp:
    """Main application class to run the export process."""
    def __init__(self):
        self.args = parse_args()
        self.client = ConfluenceClient(self.args.base_url,
                                       self.args.username,
                                       self.args.token)
        self.writer = FileWriter()
        self.converter = MarkdownConverter(self.client)

    def run(self):
        """Execute the export process."""
        page_id = self.client.extract_page_id(self.args.page_url)
        process_page(self.client, self.writer, self.converter, page_id,
                     self.args.output_dir, is_root=True)
        logger.info("Download complete.", extra={"caller": __name__})


def invoke(cls):
    """Decorator to instantiate and run the app class."""
    instance = cls()
    instance.run()
    return cls


@invoke
class MainApp(ConfluenceApp):
    pass
