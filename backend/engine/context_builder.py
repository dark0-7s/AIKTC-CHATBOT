from .extractor import extract_entities


def build_context_note(current_message: str, history: list[dict]) -> str:
    entities = extract_entities(current_message, history)

    number = entities["number"]
    number_type = entities["number_type"]
    departments = entities["departments"]
    person_intent = entities["person_intent"]
    category = entities["category"]

    # Leadership queries (Director / Principal)
    if person_intent in ("director", "principal"):
        return (
            f"Deterministic intent detected: {person_intent}. "
            f"This is a campus leadership query. "
            f"Retrieve the profile from the knowledge base and "
            f"respond using show_media_card with name, designation, initials, details, and image_url."
        )

    # Faculty / HOD queries
    if person_intent and departments:
        return (
            f"Deterministic intent detected: {person_intent} "
            f"for department {', '.join(departments)}. "
            f"This is a faculty/person query. "
            f"Retrieve the correct profile from the knowledge base and "
            f"respond using show_media_card."
        )

    if person_intent and not departments:
        return (
            f"Deterministic intent detected: {person_intent}. "
            f"The student did not specify a department. "
            f"Ask which department they mean."
        )

    # No deterministic context
    return ""