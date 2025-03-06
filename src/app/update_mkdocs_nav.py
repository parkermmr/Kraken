#!/usr/bin/env python3
"""
Update mkdocs Navigation with ruamel.yaml

This script scans the specified docs directory for Markdown (.md) files,
builds a nested navigation structure reflecting the directory hierarchy,
and writes it to the nav section in mkdocs.yml using ruamel.yaml for proper
indentation. Directories in EXCLUDED_DIRS are skipped.
"""

import os
import argparse
import logging
from ruamel.yaml import YAML

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

EXCLUDED_DIRS = {"css", "img", "javascript", "overrides", "icons"}

def build_nav_from_dir(dir_path, relative_path=""):
    """
    Recursively scan dir_path for Markdown files and return a nav structure.

    Args:
        dir_path (str): The directory to scan.
        relative_path (str): Path relative to the docs directory.

    Returns:
        list: A list of navigation items for mkdocs.yml.
    """
    nav_items = []
    try:
        entries = sorted(os.listdir(dir_path))
    except Exception as e:
        logger.error("Error listing directory %s: %s", dir_path, e)
        return nav_items

    for entry in entries:
        full_path = os.path.join(dir_path, entry)
        if os.path.isdir(full_path):
            if entry in EXCLUDED_DIRS:
                logger.debug("Excluding directory: %s", entry)
                continue
            sub_nav = build_nav_from_dir(full_path, os.path.join(relative_path, entry))
            if sub_nav:
                nav_items.append({entry: sub_nav})
        elif os.path.isfile(full_path) and entry.lower().endswith(".md"):
            if entry.lower() == "index.md":
                title = relative_path.split(os.sep)[-1] if relative_path else "Home"
            else:
                title = os.path.splitext(entry)[0]
            path_rel = os.path.join(relative_path, entry).replace("\\", "/")
            nav_items.append({title: path_rel})
    return nav_items

def update_mkdocs_nav(docs_dir, mkdocs_yaml_path):
    """
    Update the nav section of mkdocs.yml with a navigation structure
    built from the docs_dir.

    Args:
        docs_dir (str): Path to the docs directory.
        mkdocs_yaml_path (str): Path to the mkdocs.yml file.
    """
    nav_structure = build_nav_from_dir(docs_dir)
    logger.info("Built nav structure: %s", nav_structure)
    yaml = YAML()
    yaml.indent(mapping=2, sequence=4, offset=2)
    try:
        with open(mkdocs_yaml_path, "r", encoding="utf-8") as f:
            mkdocs_config = yaml.load(f)
    except Exception as e:
        logger.error("Error reading mkdocs.yml: %s", e)
        return

    mkdocs_config["nav"] = nav_structure

    try:
        with open(mkdocs_yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(mkdocs_config, f)
    except Exception as e:
        logger.error("Error writing mkdocs.yml: %s", e)
    logger.info("mkdocs.yml updated with new nav structure.")

def parse_args():
    """
    Parse command-line arguments.

    Returns:
        Namespace: Parsed arguments.
    """
    parser = argparse.ArgumentParser(description="Update mkdocs nav from docs folder")
    parser.add_argument("--docs-dir", default="docs",
                        help="Directory containing Markdown docs")
    parser.add_argument("--mkdocs-yaml", default="mkdocs.yml",
                        help="Path to mkdocs.yml file")
    return parser.parse_args()

def main():
    args = parse_args()
    update_mkdocs_nav(args.docs_dir, args.mkdocs_yaml)

if __name__ == "__main__":
    main()

