from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Dict
import re

import pdfplumber
from docx import Document

from .utils import normalize_text

@dataclass
class ParsedResume:
    raw_text: str
    sections: Dict[str, str]  # e.g., education/projects/experience
    years_experience_estimate: Optional[float] = None
    cgpa: Optional[str] = None

SECTION_HEADERS = {
    "education": [r"\beducation\b", r"\bacademics?\b", r"\bqualification(s)?\b"],
    "experience": [r"\bexperience\b", r"\bemployment\b", r"\bwork history\b", r"\binternship(s)?\b"],
    "projects": [r"\bproject(s)?\b", r"\bacademic project(s)?\b"],
    "skills": [r"\bskills?\b", r"\btechnical skills?\b", r"\bcore competencies\b"],
    "certifications": [r"\bcertification(s)?\b", r"\bcourses?\b", r"\btraining\b"],
}

def read_pdf(file_path: str) -> str:
    texts = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            t = page.extract_text() or ""
            if t.strip():
                texts.append(t)
    return normalize_text("\n".join(texts))

def read_docx(file_path: str) -> str:
    doc = Document(file_path)
    texts = [p.text for p in doc.paragraphs if p.text and p.text.strip()]
    return normalize_text("\n".join(texts))

def estimate_years_experience(text: str) -> Optional[float]:
    # Very lightweight heuristic: look for patterns like "3 years", "2.5 yrs"
    m = re.findall(r"(\d+(?:\.\d+)?)\s*(?:years|yrs)\b", text.lower())
    if not m:
        return None
    # Take max mentioned
    try:
        return max(float(x) for x in m)
    except Exception:
        return None

def extract_cgpa(text: str) -> Optional[str]:
    # Common patterns: CGPA: 8.7/10, GPA 3.8/4.0
    m = re.search(r"\b(CGPA|GPA)\b\s*[:\-]?\s*([0-9]\.?[0-9]{0,2})(\s*/\s*([0-9]{1,2}\.?[0-9]{0,2}))?", text, re.IGNORECASE)
    if not m:
        return None
    val = m.group(2)
    denom = m.group(4)
    return f"{val}/{denom}" if denom else val

def split_sections(text: str) -> Dict[str, str]:
    # Simple header-based splitting
    lines = text.splitlines()
    idxs = []
    for i, line in enumerate(lines):
        low = line.strip().lower()
        for sec, patterns in SECTION_HEADERS.items():
            for pat in patterns:
                if re.search(pat, low):
                    idxs.append((i, sec))
                    break
    if not idxs:
        return {"full": text}

    # Deduplicate close hits; keep earliest per section occurrence order in document
    idxs_sorted = sorted(idxs, key=lambda x: x[0])
    cleaned = []
    last_i = -999
    for i, sec in idxs_sorted:
        if i - last_i >= 2:  # avoid repeated headers adjacent
            cleaned.append((i, sec))
            last_i = i

    sections: Dict[str, str] = {}
    for j, (start_i, sec) in enumerate(cleaned):
        end_i = cleaned[j + 1][0] if j + 1 < len(cleaned) else len(lines)
        chunk = "\n".join(lines[start_i:end_i]).strip()
        sections[sec] = chunk

    return sections

def parse_resume(file_path: str) -> ParsedResume:
    if file_path.lower().endswith(".pdf"):
        text = read_pdf(file_path)
    elif file_path.lower().endswith(".docx"):
        text = read_docx(file_path)
    else:
        raise ValueError("Unsupported file type. Please upload PDF or DOCX.")

    sections = split_sections(text)
    yrs = estimate_years_experience(text)
    cgpa = extract_cgpa(text)
    return ParsedResume(raw_text=text, sections=sections, years_experience_estimate=yrs, cgpa=cgpa)

def parse_job_description(text: str) -> str:
    return normalize_text(text)
