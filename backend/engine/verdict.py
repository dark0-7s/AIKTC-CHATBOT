# backend/engine/verdict.py
import csv
from pathlib import Path

CUTOFFS_PATH = Path("backend/data/kb/cutoffs.csv")


def load_cutoffs() -> list[dict]:
    """Load all rows from consolidated cutoffs.csv under data/kb/ into memory."""
    rows = []
    if not CUTOFFS_PATH.exists():
        return []

    try:
        with open(CUTOFFS_PATH, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row.get("school") or not row.get("branch") or not row.get("year"):
                    continue
                rows.append({
                    "school": row["school"].strip().lower(),
                    "branch": row["branch"].strip().upper(),
                    "category": row["category"].strip(),
                    "year": int(row["year"]),
                    "cutoff": float(row["cutoff"]),
                    "cutoff_unit": row["cutoff_unit"].strip().lower()
                })
    except Exception as e:
        pass
    return rows


_CUTOFFS_CACHE: list[dict] = []


def get_cutoffs() -> list[dict]:
    """Return cached cutoffs, loading if empty."""
    global _CUTOFFS_CACHE
    if not _CUTOFFS_CACHE:
        _CUTOFFS_CACHE = load_cutoffs()
    return _CUTOFFS_CACHE


def reload_cutoffs(path: Path | None = None):
    """Force reload from disk (called after CSV upload)."""
    global _CUTOFFS_CACHE, CUTOFFS_PATH
    if path is not None:
        CUTOFFS_PATH = Path(path)
    _CUTOFFS_CACHE = load_cutoffs()


def compute_verdict(
    department: str,
    number: float,
    number_type: str,
    category: str,
    n_years: int = 4
) -> dict | None:
    """
    Compute HIGH/MEDIUM/LOW verdict for a student's score vs historical cutoffs.
    
    Returns None if no matching rows found (unexpected department/category).
    
    CRITICAL: never compare percentile against marks cutoffs or vice versa.
    cutoff_unit must match number_type:
      - "percentile" number → only percentile rows
      - "marks" number → only marks rows (Architecture/NATA)
    
    Verdict logic:
      HIGH:   score >= max cutoff in last n_years
      MEDIUM: score >= min cutoff in last n_years (but below max)
      LOW:    score < min cutoff in last n_years
    """
    rows = get_cutoffs()
    
    # Determine expected unit
    expected_unit = "jee_percentile" if number_type == "jee_percentile" else ("percentile" if number_type == "percentile" else "marks")
    
    # Filter to matching rows case-insensitively for safety
    relevant = [
        r for r in rows
        if r["branch"].upper() == department.upper()
        and r["category"].lower() == category.lower()
        and r["cutoff_unit"] == expected_unit
    ]
    
    # Take last n_years
    relevant_sorted = sorted(relevant, key=lambda r: r["year"], reverse=True)
    recent = relevant_sorted[:n_years]
    
    if not recent:
        return None
    
    cutoff_values = [r["cutoff"] for r in recent]
    min_cutoff = min(cutoff_values)
    max_cutoff = max(cutoff_values)
    
    if number >= max_cutoff:
        verdict = "HIGH"
    elif number >= min_cutoff:
        verdict = "MEDIUM"
    else:
        verdict = "LOW"
    
    return {
        "verdict": verdict,
        "min_cutoff": min_cutoff,
        "max_cutoff": max_cutoff,
        "recent_cutoffs": recent,
        "unit": expected_unit
    }


def compute_alternatives(
    number: float,
    number_type: str,
    category: str,
    exclude_depts: list[str],
    n_years: int = 4
) -> list[dict]:
    """
    Find all departments (excluding those already queried) where the
    student would score HIGH or MEDIUM. Used in single-dept predictions
    and all-LOW multi-dept follow-up.
    
    Returns sorted list (HIGH first, then MEDIUM, then by avg cutoff desc).
    """
    rows = get_cutoffs()
    expected_unit = "jee_percentile" if number_type == "jee_percentile" else ("percentile" if number_type == "percentile" else "marks")
    
    # Normalize exclude_depts to uppercase
    exclude_depts_upper = [d.upper() for d in exclude_depts]
    
    all_depts = {r["branch"].upper() for r in rows if r["cutoff_unit"] == expected_unit}
    alternatives = []
    
    for dept in all_depts:
        if dept in exclude_depts_upper:
            continue
        result = compute_verdict(dept, number, number_type, category, n_years)
        if result and result["verdict"] in ("HIGH", "MEDIUM"):
            alternatives.append({
                "dept": dept,
                "verdict": result["verdict"],
                "avg_cutoff": round(
                    sum(r["cutoff"] for r in result["recent_cutoffs"]) /
                    len(result["recent_cutoffs"]), 2
                )
            })
    
    # Sort: HIGH before MEDIUM, then by avg_cutoff descending
    alternatives.sort(
        key=lambda x: (0 if x["verdict"] == "HIGH" else 1, -x["avg_cutoff"])
    )
    return alternatives[:5]  # Cap at 5 alternatives