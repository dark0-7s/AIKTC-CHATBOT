# backend/kb/loader.py
"""
AIKTC AI Chatbot — Knowledge Base Loader
==========================================
Loads the modular JSON knowledge base from the data/kb/ directory.

Modular structure (new, canonical):
  data/kb/
  ├── common.json
  ├── engineering/
  │   ├── overview.json
  │   ├── fees.json
  │   ├── refund_policy.json
  │   └── departments/          ← one JSON file per department
  ├── pharmacy/
  │   ├── overview.json
  │   ├── fees.json
  │   ├── refund_policy.json
  │   └── departments/
  └── architecture/
      ├── overview.json
      ├── fees.json
      ├── refund_policy.json
      └── departments/

Legacy flat files (fallback, kept for compatibility):
  data/kb/engineering.json
  data/kb/pharmacy.json
  data/kb/architecture.json

The loader always tries the modular structure first. If a school's
subdirectory does not exist it falls back to the legacy flat file.

Internal format returned to the rest of the system (unchanged):
  {
    "common":       {...},
    "engineering":  {"departments": [...], "placements": {...}, "admission_process": {...}},
    "pharmacy":     {"departments": [...], ...},
    "architecture": {"departments": [...], ...},
  }
"""

import json
import csv
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger("aiktc.kb.loader")

# Schools that have a modular subfolder structure
MODULAR_SCHOOLS = ("engineering", "pharmacy", "architecture")

# Flat files loaded at root level
ROOT_FILES = ("common", "activities", "placements_stats", "cap")


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _load_json(path: Path) -> Any:
    """Load a single JSON file. Returns {} on any error."""
    try:
        with open(path, encoding="utf-8-sig") as f:
            data = json.load(f)
        logger.debug("Loaded: %s", path.name)
        return data
    except FileNotFoundError:
        logger.debug("Not found (skipped): %s", path)
        return {}
    except json.JSONDecodeError as e:
        logger.error("Invalid JSON in %s: %s", path.name, e)
        return {}
    except Exception as e:
        logger.error("Failed to load %s: %s", path.name, e)
        return {}


def _load_departments(dept_dir: Path) -> list[dict]:
    """
    Load all *.json files from a departments/ subdirectory.
    Each file is expected to be a single department dict.
    Returns an alphabetically sorted list (by file name) of depts.
    """
    if not dept_dir.is_dir():
        return []

    depts = []
    for json_file in sorted(dept_dir.glob("*.json")):
        dept = _load_json(json_file)
        if dept:
            depts.append(dept)

    logger.debug("Loaded %d departments from %s", len(depts), dept_dir)
    return depts


# ─────────────────────────────────────────────────────────────────────────────
# Modular school loader
# ─────────────────────────────────────────────────────────────────────────────

def _load_modular_school(school_dir: Path) -> dict:
    """
    Load a school from its modular subfolder.

    Merges overview + fees + refund_policy + all departments into one dict.
    The result is placed under the school key in the top-level KB.
    """
    overview       = _load_json(school_dir / "overview.json")
    fees           = _load_json(school_dir / "fees.json")
    refund_policy  = _load_json(school_dir / "refund_policy.json")
    departments    = _load_departments(school_dir / "departments")

    merged = dict(overview)                     # Start with overview fields
    if fees:
        merged["fees"] = fees
    if refund_policy:
        merged["refund_policy"] = refund_policy
    if departments:
        merged["departments"] = departments     # Always include under same key

    return merged


# ─────────────────────────────────────────────────────────────────────────────
# Legacy flat-file school loader (fallback)
# ─────────────────────────────────────────────────────────────────────────────

def _load_legacy_school(kb_path: Path, school: str) -> dict:
    """Load the old single-file school JSON (e.g. engineering.json)."""
    flat_file = kb_path / f"{school}.json"
    if flat_file.exists():
        logger.info("Using legacy flat file for school: %s", school)
        return _load_json(flat_file)
    return {}


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def _load_cutoffs_for_departments(kb_path: Path) -> tuple[dict[str, dict], dict[str, dict]]:
    """
    Read segregated CSV files and map branch -> cutoffs details separately for MHT-CET and JEE.
    """
    temp_mhtcet = {}
    temp_jee = {}

    csv_files = [p for p in kb_path.rglob("*.csv") if p.name != "cutoffs.csv"]
    if not csv_files:
        return {}, {}

    for csv_file in csv_files:
        try:
            with open(csv_file, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if not row.get("branch") or not row.get("year") or not row.get("cutoff"):
                        continue
                    branch = row["branch"].strip().upper()
                    year = int(row["year"])
                    category = row["category"].strip()
                    cutoff = float(row["cutoff"])
                    unit = row["cutoff_unit"].strip().lower()

                    target = temp_jee if unit == "jee_percentile" else temp_mhtcet

                    if branch not in target:
                        target[branch] = {}

                    if year not in target[branch]:
                        target[branch][year] = {}

                    target[branch][year][category] = cutoff
        except Exception as e:
            logger.error(f"Failed to load cutoffs from {csv_file}: {e}")

    def format_grouped(temp_dict):
        res = {}
        for branch, years in temp_dict.items():
            branch_cutoffs = []
            for year in sorted(years.keys(), reverse=True):
                year_data = {"year": year}
                for cat, val in years[year].items():
                    year_data[cat.lower()] = val
                branch_cutoffs.append(year_data)
            res[branch] = {"cutoffs": branch_cutoffs}
        return res

    return format_grouped(temp_mhtcet), format_grouped(temp_jee)


def load_and_merge_kb(kb_dir: str) -> dict:
    """
    Load and merge all knowledge base files from the given directory.

    Tries the modular subfolder structure first, falls back to the legacy
    flat file if no subfolder exists for that school.

    Args:
        kb_dir: Path to the root KB directory (e.g. 'backend/data/kb')

    Returns:
        dict: Merged KB ready for use by the rest of the system:
              {"common": {...}, "engineering": {...}, "pharmacy": {...}, "architecture": {...}}
    """
    kb_path = Path(kb_dir)
    merged: dict = {}

    if not kb_path.exists():
        logger.error("KB directory not found: %s", kb_dir)
        return {key: {} for key in (*ROOT_FILES, *MODULAR_SCHOOLS)}

    # ── Root-level flat files (e.g. common.json) ──────────────────────────
    for key in ROOT_FILES:
        merged[key] = _load_json(kb_path / f"{key}.json")

    # ── Per-school: modular folder or legacy flat file ─────────────────────
    for school in MODULAR_SCHOOLS:
        school_dir = kb_path / school
        if school_dir.is_dir():
            logger.info("Loading modular KB for school: %s", school)
            merged[school] = _load_modular_school(school_dir)
        else:
            merged[school] = _load_legacy_school(kb_path, school)

        if not merged[school]:
            logger.warning("No KB data found for school: %s", school)

    # Load cutoffs from CSV and inject into departments
    mhtcet_cutoffs, jee_cutoffs = _load_cutoffs_for_departments(kb_path)

    school_list = ["engineering", "pharmacy", "architecture"] if "engineering" in merged else ("engineering", "pharmacy", "architecture")
    for school_key in ["engineering", "pharmacy", "architecture"]:
        school_data = merged.get(school_key, {})
        if not school_data:
            continue
        for dept in school_data.get("departments", []):
            code = dept.get("code", "").upper()
            
            canonical_code = code
            if canonical_code == "COMP":
                canonical_code = "CSE"
            elif canonical_code == "BPHARM":
                canonical_code = "BPHARM"
            elif canonical_code == "BARCH":
                canonical_code = "BARCH"
                
            if canonical_code in mhtcet_cutoffs:
                dept["cutoffs"] = mhtcet_cutoffs[canonical_code]["cutoffs"]
                dept["cutoff_unit"] = "percentile"
            if canonical_code in jee_cutoffs:
                dept["jee_cutoffs"] = jee_cutoffs[canonical_code]["cutoffs"]
                
    return merged


def reload_kb(kb_dir: str) -> dict:
    """
    Force reload the knowledge base from disk.
    Use this after updating JSON files without restarting the server.

    Args:
        kb_dir: Path to the KB directory

    Returns:
        dict: Freshly loaded KB
    """
    logger.info("Reloading knowledge base from: %s", kb_dir)
    return load_and_merge_kb(kb_dir)