from __future__ import annotations
import re
from pathlib import Path
from typing import List

def normalize_text(text: str) -> str:
    text = text.replace("\u00a0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def tokenize_simple(text: str) -> List[str]:
    # Simple tokenization for keyword overlap
    text = text.lower()
    text = re.sub(r"[^a-z0-9+\-/\. ]+", " ", text)
    return [t for t in text.split() if len(t) > 1]

def load_lines(path: str | Path) -> List[str]:
    p = Path(path)
    return [line.strip() for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]
