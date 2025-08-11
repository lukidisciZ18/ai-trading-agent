from __future__ import annotations
import re
from typing import Iterable

# Simple keyword-based positive catalyst scoring
POSITIVE_PATTERNS = [
    r"\bFDA\b",
    r"\bapproval\b",
    r"\bPDUFA\b",
    r"\bphase\s*(III|3)\b",
    r"\bM&A\b|\bmerger\b|\bacquisition\b|\bbuyout\b",
    r"\bearnings\b\s*(beat|surprise|smash)\b",
    r"\bEPS\b\s*(beat|surprise)\b",
    r"\brevenue\b\s*(beat|record)\b",
    r"\bguidance\b\s*(raise|raised|hike)\b",
    r"\bpartnership\b|\bcontract\b|\bdeal\b",
]

COMPILED = [re.compile(p, re.IGNORECASE) for p in POSITIVE_PATTERNS]

def catalyst_score(texts: Iterable[str]) -> float:
    if not texts:
        return 0.0
    score = 0
    total = 0
    for t in texts:
        total += 1
        if not t:
            continue
        hits = sum(1 for rx in COMPILED if rx.search(t or ""))
        if hits > 0:
            score += 1
    if total == 0:
        return 0.0
    return min(max(score / total, 0.0), 1.0)
