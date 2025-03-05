"""
Module: markdown_parser_config.py

Defines the tag handlers mapping for the MarkdownParser.
"""

from typing import Dict

TAG_HANDLERS: Dict[str, str] = {
    "h1": "handle_heading",
    "h2": "handle_heading",
    "h3": "handle_heading",
    "h4": "handle_heading",
    "h5": "handle_heading",
    "h6": "handle_heading",
    "p": "handle_paragraph",
    "ul": "handle_ul",
    "ol": "handle_ol",
    "li": "handle_li",
    "code": "handle_code",
    "pre": "handle_pre",
    "strong": "handle_strong",
    "em": "handle_em",
    "u": "handle_u",
    "del": "handle_del",
    "ac:emoticon": "handle_ac_emoticon",
    "ac:task-list": "handle_ac_task_list",
    "ac:task": "handle_ac_task",
    "ac:task-body": "handle_ac_task_body",
    "img": "handle_img",
    "ac:image": "handle_ac_image",
    "ac:structured-macro": "handle_ac_structured_macro",
}
