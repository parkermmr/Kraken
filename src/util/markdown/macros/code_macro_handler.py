import re
from typing import Optional


class CodeMacroHandler:
    """
    Manages extraction of code macro content.
    """

    def __init__(self) -> None:
        """
        Prepare to track code macro state.
        """
        self.in_code_macro: bool = False
        self.in_code_body: bool = False
        self.start_offset: Optional[int] = None

    def begin_code_macro(self, offset: int) -> None:
        """
        Mark the start of a code macro at the given offset.
        """
        self.in_code_macro = True
        self.start_offset = offset

    def begin_code_body(self) -> None:
        """
        Switch to code body mode.
        """
        self.in_code_body = True

    def end_code_body(self) -> None:
        """
        Switch off code body mode.
        """
        self.in_code_body = False

    def finalize(self, raw_html: str, offset: int) -> str:
        """
        Collect the snippet from the start offset to the current offset,
        parse out the text within <ac:plain-text-body>, decode CDATA if present,
        return a fenced code block.
        """
        snippet: str = ""
        if self.start_offset is not None:
            snippet = raw_html[self.start_offset : offset]
        begin: int = snippet.lower().find("<ac:plain-text-body>")
        text: str = ""
        if begin != -1:
            end: int = snippet.lower().find("</ac:plain-text-body>", begin)
            if end != -1:
                after: int = snippet.find(">", begin) + 1
                text = snippet[after:end].strip()
        cdata_pat: re.Pattern = re.compile(r"^<!\[CDATA\[(.*)\]\]>$", re.DOTALL)
        match: Optional[re.Match] = cdata_pat.match(text)
        if match:
            text = match.group(1).lstrip("\n\r").rstrip()
        block: str = "\n```plaintext\n" + text + "\n```\n"
        self.reset()
        return block

    def reset(self) -> None:
        """
        Reset code macro tracking.
        """
        self.in_code_macro = False
        self.in_code_body = False
        self.start_offset = None
