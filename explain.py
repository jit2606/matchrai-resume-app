from __future__ import annotations
from typing import Dict, List
from .scoring import MatchScores, score_to_percent

def build_summary(scores: MatchScores, gaps: Dict[str, List[str]], cgpa: str | None) -> Dict[str, str]:
    matched = gaps.get("matched", [])
    missing = gaps.get("missing", [])

    return {
        "final": f"{score_to_percent(scores.final_score)}%",
        "semantic": f"{score_to_percent(scores.semantic_score)}% ({scores.method})",
        "ats": f"{score_to_percent(scores.ats_score)}%",
        "matched_skills": ", ".join(matched[:20]) + ("..." if len(matched) > 20 else ""),
        "missing_skills": ", ".join(missing[:20]) + ("..." if len(missing) > 20 else ""),
        "cgpa": cgpa or "Not detected",
    }

def recommendation_text(missing_skills: List[str]) -> str:
    if not missing_skills:
        return "Your resume already covers most skills from the job description. Focus on impact metrics and role-specific keywords."
    top = missing_skills[:8]
    return (
        "Consider adding or strengthening evidence for these missing skills (projects, coursework, internships):\n"
        + "\n".join([f"- {s}" for s in top])
        + ("\n\n(For Phase-3: we can link to curated learning resources per skill.)")
    )
