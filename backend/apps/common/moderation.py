from __future__ import annotations

import re

BLOCKED_PATTERNS = [
    r"\b(scam|fraud|phishing|malware|exploit|credential stuffing)\b",
    r"\b(hate|racist|sexist|nazi)\b",
    r"\b(adult explicit|porn|xxx|sex)\b",
    r"\b(bomb|weapon|kill|terror)\b",
    r"\b(illegal|drug trafficking|money laundering)\b",
]


def moderate_text(text: str) -> tuple[bool, str | None]:
    normalized = text.lower()
    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, normalized):
            return False, "Prompt blocked by safety moderation."
    return True, None
