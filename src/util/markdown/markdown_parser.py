"""
Module: markdown_parser.py

Provides the MarkdownParser class to convert Confluence HTML into Markdown.
Non-table content is transformed into Markdown, while table HTML is preserved
and later processed to render Confluence tasks as HTML checkboxes. It also
extracts content from Confluence code macros into fenced code blocks, and
derives the actual image filename for Gliffy diagrams from parameters.
"""

import re
from html.parser import HTMLParser
from typing import Any, Dict, List, Optional, Tuple

from src.util.markdown.macros.code_macro_handler import CodeMacroHandler
from src.util.markdown.macros.gliffy_macro_handler import GliffyMacroHandler
from src.util.markdown.macros.table_html_transformer import \
    transform_table_html
from src.util.markdown.parser_config import TAG_HANDLERS
from src.util.utils import decode_literal_unicode_escapes, sanitize_title


class MarkdownParser(HTMLParser):
    """
    Parses Confluence HTML into Markdown, preserving table HTML,
    handling code macros, gliffy macros, tasks as checkboxes, and more.
    """

    def __init__(self, client: Any) -> None:
        """
        Initialize the MarkdownParser.
        """
        super().__init__()
        self.client: Any = client
        self.output: List[str] = []
        self.tag_stack: List[str] = []
        self.config: Dict[str, str] = TAG_HANDLERS.copy()
        self.in_code_block: bool = False
        self.list_stack: List[Tuple[str, int]] = []
        self.in_list_item: bool = False
        self.list_item_buffer: List[str] = []
        self.task_status: Optional[str] = None
        self.in_task_body: bool = False
        self.task_body_buffer: List[str] = []
        self.in_table_mode: bool = False
        self.table_depth: int = 0
        self.table_html: List[str] = []

        self.code_macro: CodeMacroHandler = CodeMacroHandler()
        self.gliffy_macro: GliffyMacroHandler = GliffyMacroHandler()

    def get_markdown(self) -> str:
        """
        Return the processed Markdown text.
        """
        joined: str = "".join(self.output)
        return self._post_process_output(joined)

    def _post_process_output(self, text_in: str) -> str:
        """
        Post-process the output, decoding Unicode escapes and converting links.
        """

        def clean_heading(match: re.Match) -> str:
            return match.group(0).replace("**", "")

        def transform_links(txt: str) -> str:
            pat: re.Pattern = re.compile(r"(https?://\S+)")
            return pat.sub(r"[Click Me ️👆](\1#code)", txt)

        text: str = re.sub(
            r"^(#+\s+.*)$", lambda m: clean_heading(m), text_in, flags=re.MULTILINE
        )
        text = re.sub(r"(?<!\n)(!\[)", r"\n\1", text)
        text = re.sub(r"(\]\(images/[^)]+\))", r"\1\n", text)
        text = re.sub(r"^src:\s*", "", text, flags=re.MULTILINE)
        lines: List[str] = [ln.rstrip() for ln in text.splitlines()]
        final: str = "\n".join(lines)
        final = decode_literal_unicode_escapes(final)
        final = transform_links(final)
        return final

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        """
        Handle the start of an HTML tag.
        """
        t: str = tag.lower()
        if self.in_table_mode:
            self._append_table_html(self.get_starttag_text())
            if t == "table":
                self.table_depth += 1
            self.tag_stack.append(t)
            return

        self.tag_stack.append(t)
        if t == "ac:structured-macro":
            mapped: Dict[str, str] = {k: v for k, v in attrs if v}
            name: str = mapped.get("ac:name", "").lower()
            if name == "code":
                self.code_macro.begin_code_macro(self._raw_offset())
            if name == "gliffy":
                self.gliffy_macro.begin_gliffy(self._raw_offset())

        if self.code_macro.in_code_macro and t == "ac:plain-text-body":
            self.code_macro.begin_code_body()

        method_n: str = self.config.get(t, "default_start_handler")
        method = getattr(self, method_n, self.default_start_handler)
        method(t, dict(attrs))
        if t == "table":
            self._start_table_mode(self.get_starttag_text())

    def handle_endtag(self, tag: str) -> None:
        """
        Handle the end of an HTML tag.
        """
        t: str = tag.lower()
        if self.in_table_mode:
            self._append_table_html(f"</{t}>")
            if t == "table":
                self.table_depth -= 1
                if self.table_depth == 0:
                    self._end_table_mode()
            if t in self.tag_stack:
                self.tag_stack.remove(t)
            return

        if t in self.tag_stack:
            self.tag_stack.remove(t)

        if self.code_macro.in_code_macro and t == "ac:plain-text-body":
            self.code_macro.end_code_body()

        if self.code_macro.in_code_macro and t == "ac:structured-macro":
            final: str = self.code_macro.finalize(self.rawdata, self._raw_offset())
            self.output.append(final)

        if self.gliffy_macro.in_gliffy and t == "ac:structured-macro":
            gliffy_block: str = self.gliffy_macro.finalize(
                self.rawdata, self._raw_offset()
            )
            self.output.append(gliffy_block)

        method_n: str = self.config.get(t, "default_end_handler") + "_end"
        method = getattr(self, method_n, self.default_end_handler)
        method(t)

    def handle_startendtag(
        self, tag: str, attrs: List[Tuple[str, Optional[str]]]
    ) -> None:
        """
        Handle a self-closing HTML tag.
        """
        t: str = tag.lower()
        if self.in_table_mode:
            self._append_table_html(self.get_starttag_text())
            return
        method_n: str = self.config.get(t, "default_self_handler")
        method = getattr(self, method_n, self.default_self_handler)
        method(t, dict(attrs))

    def handle_data(self, data: str) -> None:
        """
        Handle textual data in the HTML, skipping data
        inside code/gliffy macros to avoid leftover IDs.
        """
        if self.code_macro.in_code_macro and not self.code_macro.in_code_body:
            return
        if self.gliffy_macro.in_gliffy:
            return
        if self.in_table_mode:
            self._append_table_html(data)
        else:
            c: str = data.strip()
            if c:
                self._append_text(c)

    def default_start_handler(self, tag: str, attrs: Dict[str, Optional[str]]) -> None:
        """
        Default handler for start tags.
        """
        pass

    def default_end_handler(self, tag: str) -> None:
        """
        Default handler for end tags.
        """
        pass

    def default_self_handler(self, tag: str, attrs: Dict[str, Optional[str]]) -> None:
        """
        Default handler for self-closing tags.
        """
        pass

    def _start_table_mode(self, raw_tag: str) -> None:
        """
        Enter table mode to capture raw table HTML.
        """
        self.in_table_mode = True
        self.table_depth = 1
        self.table_html = []
        self._append_table_html(raw_tag)

    def _end_table_mode(self) -> None:
        """
        Exit table mode and process the table HTML.
        """
        self.in_table_mode = False
        joined: str = "".join(self.table_html)
        final: str = transform_table_html(joined)
        self.output.append("\n" + final + "\n")
        self.table_html = []

    def _append_table_html(self, content: str) -> None:
        """
        Append content to the table HTML buffer.
        """
        self.table_html.append(content)

    def _append_text(self, text: str) -> None:
        """
        Append text to the output, handling inline formatting.
        """
        if self._in_inline_formatting():
            text = text.rstrip()
        if self.in_list_item:
            self.list_item_buffer.append(text)
        elif self.in_task_body:
            self.task_body_buffer.append(text)
        else:
            self.output.append(text)

    def _in_inline_formatting(self) -> bool:
        """
        Return whether currently in inline formatting tags.
        """
        inline: set = {"strong", "b", "em", "i", "u", "del", "strike"}
        return any(tag in self.tag_stack for tag in inline)

    def _raw_offset(self) -> int:
        """
        Return the absolute offset in self.rawdata from current parser position.
        """
        line, col = self.getpos()
        splitted: List[str] = self.rawdata.splitlines(True)
        if line - 1 < len(splitted):
            before: int = sum(len(ln) for ln in splitted[: line - 1])
            return before + col
        return len(self.rawdata)

    def handle_heading(self, tag: str, attrs: Dict[str, Optional[str]]) -> None:
        """
        Handle heading tags.
        """
        level_str: str = tag[1] if len(tag) > 1 else "1"
        try:
            lv: int = int(level_str)
        except ValueError:
            lv = 1
        self._append_text("\n" + "#" * lv + " ")

    def handle_paragraph(self, tag: str, attrs: Dict[str, Optional[str]]) -> None:
        """
        Handle paragraph tags.
        """
        self._append_text("\n\n")

    def handle_ul(self, tag: str, attrs: Dict[str, Optional[str]]) -> None:
        """
        Handle unordered list start.
        """
        self.list_stack.append(("ul", 0))
        self._append_text("\n")

    def handle_ul_end(self, tag: str) -> None:
        """
        Handle unordered list end.
        """
        if self.list_stack:
            self.list_stack.pop()

    def handle_ol(self, tag: str, attrs: Dict[str, Optional[str]]) -> None:
        """
        Handle ordered list start.
        """
        self.list_stack.append(("ol", 1))
        self._append_text("\n")

    def handle_ol_end(self, tag: str) -> None:
        """
        Handle ordered list end.
        """
        if self.list_stack:
            self.list_stack.pop()

    def handle_li(self, tag: str, attrs: Dict[str, Optional[str]]) -> None:
        """
        Handle list item start.
        """
        self.in_list_item = True
        self.list_item_buffer = []

    def handle_li_end(self, tag: str) -> None:
        """
        Handle list item end.
        """
        self.in_list_item = False
        prefix: str = "- "
        if self.list_stack:
            typ, count = self.list_stack[-1]
            if typ == "ul":
                prefix = "- "
            else:
                prefix = f"{count}. "
                self.list_stack[-1] = (typ, count + 1)
        content: str = "".join(self.list_item_buffer).strip()
        self.output.append(f"\n{prefix}{content}")

    def handle_code(self, tag: str, attrs: Dict[str, Optional[str]]) -> None:
        """
        Handle inline code start.
        """
        self._append_text(" `")

    def handle_code_end(self, tag: str) -> None:
        """
        Handle inline code end.
        """
        self._append_text("` ")

    def handle_pre(self, tag: str, attrs: Dict[str, Optional[str]]) -> None:
        """
        Handle code block start.
        """
        self.in_code_block = True
        self._append_text("\n```\n")

    def handle_pre_end(self, tag: str) -> None:
        """
        Handle code block end.
        """
        self.in_code_block = False
        self._append_text("\n```\n")

    def handle_strong(self, tag: str, attrs: Dict[str, Optional[str]]) -> None:
        """
        Handle strong text start.
        """
        self._append_text(" **")

    def handle_strong_end(self, tag: str) -> None:
        """
        Handle strong text end.
        """
        self._append_text("** ")

    def handle_em(self, tag: str, attrs: Dict[str, Optional[str]]) -> None:
        """
        Handle emphasized text start.
        """
        self._append_text(" _")

    def handle_em_end(self, tag: str) -> None:
        """
        Handle emphasized text end.
        """
        self._append_text("_ ")

    def handle_u(self, tag: str, attrs: Dict[str, Optional[str]]) -> None:
        """
        Handle underline text start.
        """
        self._append_text(" <u>")

    def handle_u_end(self, tag: str) -> None:
        """
        Handle underline text end.
        """
        self._append_text("</u> ")

    def handle_del(self, tag: str, attrs: Dict[str, Optional[str]]) -> None:
        """
        Handle deleted text start.
        """
        self._append_text(" ~~")

    def handle_del_end(self, tag: str) -> None:
        """
        Handle deleted text end.
        """
        self._append_text("~~ ")

    def handle_ac_emoticon(self, tag: str, attrs: Dict[str, Optional[str]]) -> None:
        """
        Handle Confluence emoticon tags.
        """
        fb: str = attrs.get("ac:emoji-fallback", "")
        sn: str = attrs.get("ac:emoji-shortname", "")
        if fb:
            self._append_text(fb)
        elif sn:
            self._append_text(sn)

    def handle_ac_emoticon_end(self, tag: str) -> None:
        """
        Handle emoticon end tag.
        """
        pass

    def handle_ac_task_list(self, tag: str, attrs: Dict[str, Optional[str]]) -> None:
        """
        Handle task list start.
        """
        self._append_text("\n")

    def handle_ac_task_list_end(self, tag: str) -> None:
        """
        Handle task list end.
        """
        self._append_text("\n")

    def handle_ac_task(self, tag: str, attrs: Dict[str, Optional[str]]) -> None:
        """
        Handle task start.
        """
        self.task_status = attrs.get("ac:task-status", "incomplete").lower()
        self.in_task_body = True
        self.task_body_buffer = []

    def handle_ac_task_end(self, tag: str) -> None:
        """
        Handle task end and append formatted task.
        """
        cbox: str = "[x]" if self.task_status == "complete" else "[ ]"
        combined: str = "".join(self.task_body_buffer).strip()
        final: str = re.sub(
            r"^[0-9]+\s*(complete|incomplete)\s*", "", combined, flags=re.IGNORECASE
        )
        self.output.append(f"\n- {cbox} {final}")
        self.in_task_body = False
        self.task_body_buffer = []
        self.task_status = None

    def handle_ac_task_body(self, tag: str, attrs: Dict[str, Optional[str]]) -> None:
        """
        Handle task body start.
        """
        self.in_task_body = True

    def handle_ac_task_body_end(self, tag: str) -> None:
        """
        Handle task body end.
        """
        self.in_task_body = False

    def handle_img(self, tag: str, attrs: Dict[str, Optional[str]]) -> None:
        """
        Handle image tags.
        """
        alt: str = attrs.get("alt", "").strip() or "image"
        s: str = sanitize_title(alt)
        self._append_text(f"\n![{s}](images/{s})\n")

    def handle_ac_image(self, tag: str, attrs: Dict[str, Optional[str]]) -> None:
        """
        Handle ac:image tags.
        """
        alt: str = (
            attrs.get("ac:alt", "").strip()
            or attrs.get("ri:filename", "").strip()
            or "image"
        )
        s: str = sanitize_title(alt)
        self._append_text(f"\n![{s}](images/{s})\n")

    def handle_ac_structured_macro(
        self, tag: str, attrs: Dict[str, Optional[str]]
    ) -> None:
        """
        Handle structured macros. Code and gliffy macros are processed
        in handle_endtag. All others produce a single space.
        """
        mac: str = attrs.get("ac:name", "").lower()
        if mac not in ("code", "gliffy"):
            self._append_text(" ")

    def _getpos_in_rawdata(self) -> int:
        """
        Return the absolute offset in rawdata based on current parser position.
        """
        line, col = self.getpos()
        splitted: List[str] = self.rawdata.splitlines(True)
        if line - 1 < len(splitted):
            before: int = sum(len(ln) for ln in splitted[: line - 1])
            return before + col
        return len(self.rawdata)
