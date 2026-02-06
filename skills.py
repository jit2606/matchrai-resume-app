from __future__ import annotations
from typing import List, Set, Dict
import re

from .utils import load_lines, normalize_text

def build_skill_taxonomy(path: str) -> List[str]:
    skills = load_lines(path)
    # Normalize to lowercase for matching
    return sorted({normalize_text(s).lower() for s in skills}, key=len, reverse=True)

def extract_skills(text: str, taxonomy: List[str]) -> List[str]:
    """
    Extract skills by exact/near-exact substring matches.
    This is intentionally simple for Phase-2 PoC.
    """
    low = " " + text.lower() + " "
    found: Set[str] = set()

    # Word-boundary matching for single tokens, substring for multi-word skills
    for skill in taxonomy:
        if " " in skill or "-" in skill or "+" in skill:
            if skill in low:
                found.add(skill)
        else:
            if re.search(rf"\b{re.escape(skill)}\b", low):
                found.add(skill)

    return sorted(found)

def keyword_gaps(resume_text: str, jd_text: str, taxonomy: List[str]) -> Dict[str, List[str]]:
    resume_sk = set(extract_skills(resume_text, taxonomy))
    jd_sk = set(extract_skills(jd_text, taxonomy))

    missing = sorted(jd_sk - resume_sk)
    matched = sorted(jd_sk & resume_sk)
    extra = sorted(resume_sk - jd_sk)

    return {"matched": matched, "missing": missing, "extra": extra}
