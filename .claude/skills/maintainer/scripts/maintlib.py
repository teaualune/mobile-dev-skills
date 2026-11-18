"""Shared helpers for the maintainer scripts (imported by path; see each script's sys.path line)."""
import argparse
import os
import re
import sys
import unicodedata

SCRIPT_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."))

# Invisible, bidi, line-separator, variation-selector and tag characters; built from code points so no file holds them.
HIDDEN_RANGES = (
    (0x00AD, 0x00AD), (0x061C, 0x061C), (0x180E, 0x180E), (0x200B, 0x200F), (0x2028, 0x202E),
    (0x2060, 0x2064), (0x2066, 0x2069), (0xFE00, 0xFE0F), (0xFEFF, 0xFEFF),
    (0xE0000, 0xE007F), (0xE0100, 0xE01EF),
)
HIDDEN = re.compile("[" + "".join(f"{chr(a)}-{chr(b)}" for a, b in HIDDEN_RANGES) + "]")
EMOJI_JOINERS = {0x200D, 0xFE0E, 0xFE0F}


def _symbol(ch):
    return unicodedata.category(ch) == "So"


def hidden_chars(text):
    """Yield (index, codepoint) of hidden characters, skipping ZWJ / VS15 / VS16 inside emoji sequences."""
    for m in HIDDEN.finditer(text):
        i, cp = m.start(), ord(m.group())
        if cp in EMOJI_JOINERS and i > 0:
            prev = text[i - 1]
            if cp == 0x200D:
                if i > 1 and ord(prev) in (0xFE0F, 0xFE0E):
                    prev = text[i - 2]
                if _symbol(prev) and i + 1 < len(text) and _symbol(text[i + 1]):
                    continue
            elif _symbol(prev):
                continue
        yield i, cp


def allowed(url, prefixes):
    return any(url == p.rstrip("/") or url.startswith(p) for p in prefixes)


SAFE_VALUE = re.compile(r"[\w.+:/,=?&%@~-]{1,200}")


def safe(value):
    """Fetched values go into KEY=VALUE output; anything else could forge a line."""
    value = str(value)
    if not value:
        return "-"
    return value if SAFE_VALUE.fullmatch(value) else "<invalid>"


def one_line(text, limit=160):
    return re.sub(r"[\x00-\x1f\x7f\s]+", " ", str(text)).strip()[:limit]


class ArgParser(argparse.ArgumentParser):
    """Usage errors exit 4, the scripts' documented config/usage code (argparse defaults to 2)."""

    def error(self, message):
        self.print_usage(sys.stderr)
        print(f"{self.prog}: error: {message}", file=sys.stderr)
        sys.exit(4)
