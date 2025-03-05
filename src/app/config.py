"""
Handles command-line argument parsing.
"""

import argparse


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Download Confluence pages as Markdown."
    )
    parser.add_argument("--base-url", required=True, help="Confluence base URL")
    parser.add_argument(
        "--page-url", required=True, help="Starting Confluence page URL"
    )
    parser.add_argument("--username", required=True, help="Confluence username/email")
    parser.add_argument("--token", required=True, help="Confluence API token")
    parser.add_argument("--output-dir", default="output", help="Output directory")
    return parser.parse_args()
