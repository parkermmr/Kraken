import re
from typing import Optional
from src.util.utils import sanitize_title


class GliffyMacroHandler:
    """
    Manages extraction of Gliffy macro content.
    """

    def __init__(self) -> None:
        """
        Prepare to track gliffy macro state.
        """
        self.in_gliffy: bool = False
        self.start_offset: Optional[int] = None

    def begin_gliffy(self, offset: int) -> None:
        """
        Mark the start of a gliffy macro at the given offset.
        """
        self.in_gliffy = True
        self.start_offset = offset

    def finalize(self, raw_html: str, offset: int) -> str:
        """
        Collect the snippet from start to offset,
        parse the diagram name out of <ac:parameter ac:name="name">, or use fallback.
        """
        snippet: str = ""
        if self.start_offset is not None:
            snippet = raw_html[self.start_offset : offset]
        pat: re.Pattern = re.compile(
            r'<ac:parameter\s+ac:name="name">\s*([^<]+)\s*</ac:parameter>',
            flags=re.IGNORECASE,
        )
        found: Optional[re.Match] = pat.search(snippet)
        diag: str = found.group(1).strip() if found else "gliffy_diagram"
        sanitized: str = sanitize_title(diag)
        ref: str = f"\n![{diag}](images/{sanitized}.png)\n"
        self.reset()
        return ref

    def reset(self) -> None:
        """
        Reset gliffy macro tracking.
        """
        self.in_gliffy = False
        self.start_offset = None
