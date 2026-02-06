from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Tuple, Dict, Any, List
import numpy as np

from .utils import tokenize_simple

# --- Optional semantic model ---
def _try_load_sentence_transformer(model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
    try:
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer(model_name)
    except Exception:
        return None

def cosine(a: np.ndarray, b: np.ndarray) -> float:
    denom = (np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)

def semantic_similarity(resume_text: str, jd_text: str, model=None) -> Tuple[float, str]:
    """
    Returns (score 0..1, method)
    """
    if model is None:
        model = _try_load_sentence_transformer()

    if model is not None:
        emb = model.encode([resume_text, jd_text], normalize_embeddings=True)
        score = float(np.dot(emb[0], emb[1]))
        return max(0.0, min(1.0, score)), "sentence-transformers"

    # Fallback: TF-IDF cosine
    from sklearn.feature_extraction.text import TfidfVectorizer
    vec = TfidfVectorizer(stop_words="english", max_features=5000)
    X = vec.fit_transform([resume_text, jd_text]).toarray()
    score = cosine(X[0], X[1])
    return max(0.0, min(1.0, score)), "tfidf"

def ats_keyword_score(resume_text: str, jd_text: str) -> float:
    """
    Simple ATS-like keyword overlap based on token sets.
    """
    r = set(tokenize_simple(resume_text))
    j = set(tokenize_simple(jd_text))
    if not j:
        return 0.0
    overlap = len(r & j) / max(1, len(j))
    return float(max(0.0, min(1.0, overlap)))

@dataclass
class MatchScores:
    semantic_score: float
    ats_score: float
    final_score: float
    method: str
    breakdown: Dict[str, Any]

def fresher_weighting(years_exp: Optional[float], fresher_mode: bool) -> Dict[str, float]:
    """
    Weights for combining semantic and ATS scores.
    - Fresher mode: slightly favors semantic match (projects/education alignment)
    - Experienced: balance or slightly favors ATS keywords (role-specific terms)
    """
    if fresher_mode or (years_exp is not None and years_exp < 2.0):
        return {"semantic": 0.70, "ats": 0.30}
    return {"semantic": 0.55, "ats": 0.45}

def compute_match(resume_text: str, jd_text: str, years_exp: Optional[float] = None, fresher_mode: bool = False) -> MatchScores:
    sem, method = semantic_similarity(resume_text, jd_text)
    ats = ats_keyword_score(resume_text, jd_text)
    w = fresher_weighting(years_exp, fresher_mode)

    final = w["semantic"] * sem + w["ats"] * ats
    final = float(max(0.0, min(1.0, final)))

    return MatchScores(
        semantic_score=sem,
        ats_score=ats,
        final_score=final,
        method=method,
        breakdown={"weights": w, "years_experience_estimate": years_exp, "fresher_mode": fresher_mode},
    )

def score_to_percent(x: float) -> int:
    return int(round(100 * max(0.0, min(1.0, x))))
