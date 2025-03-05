"""
Module: table_html_transformer.py

Transforms raw table HTML to convert Confluence tasks into HTML checkboxes.
"""

import re
from html.parser import HTMLParser
from typing import Dict, List, Optional, Tuple


def transform_table_html(table_html: str) -> str:
    """Transform table HTML to replace Confluence tasks with checkboxes."""
    transformer: TableHtmlTransformer = TableHtmlTransformer()
    transformer.feed(table_html)
    return transformer.get_output()


class TableHtmlTransformer(HTMLParser):
    """HTML parser to transform Confluence task elements into checkboxes."""

    def __init__(self) -> None:
        """Initialize the TableHtmlTransformer."""
        super().__init__()
        self.output: List[str] = []
        self.in_task_list: bool = False
        self.in_ac_task: bool = False
        self.in_task_body: bool = False
        self.in_ac_task_status: bool = False
        self.task_status: str = "incomplete"
        self.task_body_buffer: List[str] = []

    def get_output(self) -> str:
        """Return the transformed HTML output."""
        return "".join(self.output)

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        """Handle the start of an HTML tag."""
        tag_lower: str = tag.lower()
        attr_dict: Dict[str, str] = {k.lower(): v for k, v in attrs if v is not None}
        if tag_lower == "ac:task-id":
            return
        if tag_lower == "span" and "class" in attr_dict:
            if attr_dict["class"] == "placeholder-inline-tasks":
                return
        if tag_lower == "ac:task-list":
            self.in_task_list = True
            self.output.append("<ul>")
            return
        if tag_lower == "ac:task":
            self.in_ac_task = True
            self.task_status = attr_dict.get("ac:task-status", "incomplete")
            return
        if tag_lower == "ac:task-body":
            self.in_task_body = True
            return
        if tag_lower == "ac:task-status":
            self.in_ac_task_status = True
            return
        self._append_raw_tag(tag_lower, attr_dict, is_start=True)

    def handle_endtag(self, tag: str) -> None:
        """Handle the end of an HTML tag."""
        tag_lower: str = tag.lower()
        if tag_lower == "ac:task-list":
            self.in_task_list = False
            self.output.append("</ul>")
            return
        if tag_lower == "ac:task":
            text: str = "".join(self.task_body_buffer).strip()

            text = re.sub(
                r"^[0-9\.\)\(\-_\s]*(complete|incomplete)?\s*",
                "",
                text,
                flags=re.IGNORECASE,
            )
            checked: str = "checked" if self.task_status.lower() == "complete" else ""
            self.output.append(f"<li><input type='checkbox' {checked}> {text}</li>")
            self.task_body_buffer = []
            self.in_ac_task = False
            return
        if tag_lower == "ac:task-body":
            self.in_task_body = False
            return
        if tag_lower == "ac:task-status":
            self.in_ac_task_status = False
            return
        if tag_lower == "ac:task-id":
            return
        if tag_lower == "span":
            return
        self._append_raw_tag(tag_lower, {}, is_start=False)

    def handle_data(self, data: str) -> None:
        """Handle data within tags."""
        if self.in_ac_task_status:
            self.task_status = data.strip().lower()
            return
        if self.in_ac_task and not self.in_task_body and not self.in_ac_task_status:
            check_data: str = data.strip().lower()
            if re.match(r"^[0-9]+(\.|\)|\s|$)", check_data) or re.match(
                r"^[0-9]+(\.|\)|\s)*(complete|incomplete)?$", check_data
            ):
                return
        if self.in_task_body:
            self.task_body_buffer.append(data)
        else:
            self.output.append(data)

    def _append_raw_tag(self, tag: str, attrs: Dict[str, str], is_start: bool) -> None:
        """Append a raw HTML tag to the output."""
        if is_start:
            attr_str: str = " ".join(f'{k}="{v}"' for k, v in attrs.items())
            if attr_str:
                self.output.append(f"<{tag} {attr_str}>")
            else:
                self.output.append(f"<{tag}>")
        else:
            self.output.append(f"</{tag}>")
