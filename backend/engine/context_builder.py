# backend/engine/context_builder.py
from .extractor import extract_entities
from .verdict import compute_verdict, compute_alternatives


def build_context_note(current_message: str, history: list[dict]) -> str:
    """
    Main engine entry point. Called on every request.
    Returns a context note string (Type A/B/C/D/E) or empty string.

    Decision table (evaluated top-to-bottom):
      D: No number found                              → "" (LLM uses KB)
      B: rank/score + no department                  → ask for percentile
      B: rank/score + department (non-BARCH marks)   → ask for percentile
      E: ambiguous number + department               → ask percentile or rank?
      B: ambiguous number + no department            → ask both
      C: percentile/marks + no department            → ask for department
      C: percentile/marks + department + no category → ask for category (NEVER default Open)
      A: percentile/marks + department + category    → compute verdict
    """
    entities = extract_entities(current_message, history)

    number        = entities["number"]
    number_type   = entities["number_type"]
    departments   = entities["departments"]
    category      = entities["category"]
    number_source = entities["number_source"]

    # ── Type D: No number found ────────────────────────────────────
    if number is None:
        return ""  # LLM answers from KB

    dept_str = ", ".join(departments) if departments else "none"

    # ── Rank without department ────────────────────────────────────
    if number_type == "rank" and not departments:
        return (
            f"Deterministic engine extracted: number={number} "
            f"(type=rank, from {number_source}), department=none. "
            f"Confidence: LOW. No percentile provided."
        )

    # ── Rank WITH department ───────────────────────────────────────
    if number_type == "rank" and departments:
        return (
            f"Deterministic engine extracted: number={number} "
            f"(type=rank), department={dept_str}. "
            f"Confidence: LOW. MHT-CET percentile not provided."
        )

    # ── Marks: only BARCH can use marks directly ───────────────────
    if number_type == "marks":
        if departments and "BARCH" in departments:
            # Fall through to Type A logic for NATA marks
            pass
        elif departments:
            return (
                f"Deterministic engine extracted: number={number} "
                f"(type=marks), department={dept_str}. "
                f"Confidence: LOW. Marks/score provided instead of percentile."
            )
        else:
            return (
                f"Deterministic engine extracted: number={number} "
                f"(type=marks, from {number_source}), department=none. "
                f"Confidence: LOW. Department and percentile not provided."
            )

    # ── Type E: Ambiguous number WITH department ───────────────────
    if number_type == "ambiguous" and departments:
        return (
            f"Deterministic engine extracted: number={number} "
            f"(ambiguous), department={dept_str}. Confidence: LOW. "
            f"Number type (percentile or rank) not provided."
        )

    # ── Type B: Ambiguous number WITHOUT department ────────────────
    if number_type == "ambiguous" and not departments:
        return (
            f"Deterministic engine extracted: number={number} "
            f"(ambiguous), department=none. "
            f"Confidence: LOW. Number type and department not provided."
        )

    # ── Type C: Clear number, missing department ───────────────────
    if number_type in ("percentile", "marks") and not departments:
        return (
            f"Deterministic engine extracted: number={number} "
            f"({number_type}, from {number_source}), department=none. "
            f"Confidence: LOW. Department not provided."
        )

    # ── Type C: Clear number + department, missing category ────────
    if number_type in ("percentile", "marks") and departments and not category:
        return (
            f"Deterministic engine extracted: number={number} ({number_type}), "
            f"department={dept_str}. Confidence: LOW. Category not found."
        )

    # ── Type A: All fields present — compute verdict ───────────────
    if number_type in ("percentile", "marks") and departments and category:
        verdicts = []
        all_low  = True

        for dept in departments:
            result = compute_verdict(dept, number, number_type, category)
            if result is None:
                continue
            if result["verdict"] != "LOW":
                all_low = False
            verdicts.append({
                "dept"       : dept,
                "verdict"    : result["verdict"],
                "min_cutoff" : result["min_cutoff"],
                "max_cutoff" : result["max_cutoff"],
                "unit"       : result["unit"],
            })

        if not verdicts:
            return (
                f"Deterministic engine: no cutoff data found for "
                f"{', '.join(departments)} in category {category}. "
                f"LLM should acknowledge and escalate to admissions office."
            )

        # Compute alternatives list
        alternatives = []
        if all_low:
            alternatives = compute_alternatives(
                number, number_type, category,
                exclude_depts=departments
            )

        verdicts_str = "; ".join(
            f"{v['dept']} [{v['verdict']}, cutoff {v['min_cutoff']}–{v['max_cutoff']} {v['unit']}]"
            for v in verdicts
        )

        context = (
            f"Deterministic engine computed: percentile={number} "
            f"({number_type}, from {number_source}), category={category}. "
            f"Predictions: {verdicts_str}. Confidence: HIGH."
        )

        if all_low and alternatives:
            alt_str = "; ".join(
                f"{a['dept']} [{a['verdict']}, avg cutoff {a['avg_cutoff']}]"
                for a in alternatives
            )
            context += (
                f" ALL PREDICTIONS ARE LOW. "
                f"Global alternatives (departments where score qualifies): {alt_str}. "
                f"After show_multi_pred (if multiple depts) or show_prediction, "
                f"follow with show_text listing these alternatives empathetically."
            )
        elif len(verdicts) == 1 and not all_low:
            # Add alternatives for single-dept non-LOW prediction
            alt = compute_alternatives(
                number, number_type, category,
                exclude_depts=departments
            )
            if alt:
                alt_str = "; ".join(
                    f"{a['dept']} [{a['verdict']}, avg cutoff {a['avg_cutoff']}]"
                    for a in alt[:3]
                )
                context += f" Alternatives: {alt_str}."

        return context

    # Fallback — should never reach here
    return ""