# backend/prompt/functions.py

FUNCTION_DEFINITIONS = [
    {
        "name": "show_text",
        "description": (
            "Display a plain text response. Use for: general factual answers, "
            "hostel info, out-of-KB general knowledge with disclaimer, "
            "troubleshooting escalation, all-LOW multi_pred follow-up alternatives text. "
            "Do NOT use for multi-category information (e.g., placements by school) — use show_list instead."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "The complete response text. May include line breaks."
                }
            },
            "required": ["message"]
        }
    },
    {
        "name": "show_table",
        "description": (
            "Display a structured data table. Use for: historical cutoff data by year, "
            "fee breakdown by category, intake seats by department, comparison of structured "
            "rows with columns. NOT for predictions."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "columns": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Column header names"
                },
                "rows": {
                    "type": "array",
                    "items": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "description": "Each inner array is one row, same length as columns"
                }
            },
            "required": ["title", "columns", "rows"]
        }
    },
    {
        "name": "show_prediction",
        "description": (
            "Display an admission chance prediction for a SINGLE department. "
            "Use only when deterministic context is HIGH confidence and student asked for "
            "eligibility/chances for ONE department. Includes alternatives."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "dept": {"type": "string", "description": "Department code e.g. CSE"},
                "dept_name": {"type": "string", "description": "Full department name"},
                "percentile": {"type": "number"},
                "category": {"type": "string"},
                "verdict": {
                    "type": "string",
                    "enum": ["HIGH", "MEDIUM", "LOW"]
                },
                "reasoning": {
                    "type": "string",
                    "description": (
                        "2-3 sentences explaining the verdict using actual cutoff numbers. "
                        "Must cite specific cutoff values from the deterministic context."
                    )
                },
                "alternatives": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "dept": {"type": "string"},
                            "dept_name": {"type": "string"},
                            "verdict": {"type": "string", "enum": ["HIGH", "MEDIUM"]},
                            "avg_cutoff": {"type": "number"}
                        },
                        "required": ["dept", "verdict", "avg_cutoff"]
                    },
                    "description": "Only HIGH or MEDIUM alternatives. Max 5. Empty if primary verdict is HIGH."
                }
            },
            "required": ["dept", "percentile", "category", "verdict", "reasoning", "alternatives"]
        }
    },
    {
        "name": "show_multi_pred",
        "description": (
            "Display admission chance predictions for MULTIPLE departments simultaneously. "
            "Use when student asked about 2+ departments in a single message. "
            "Does NOT include alternatives[] — an all-LOW result must be followed by show_text "
            "listing alternatives from the deterministic context."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "predictions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "dept": {"type": "string"},
                            "dept_name": {"type": "string"},
                            "verdict": {"type": "string", "enum": ["HIGH", "MEDIUM", "LOW"]},
                            "cutoff_range": {
                                "type": "string",
                                "description": "e.g. '89.7–94.2 percentile (last 4 years)'"
                            },
                            "reasoning": {"type": "string"}
                        },
                        "required": ["dept", "verdict", "cutoff_range", "reasoning"]
                    },
                    "description": "One entry per requested department. No alternatives field."
                }
            },
            "required": ["predictions"]
        }
    },
    {
        "name": "show_media_card",
        "description": (
            "Display a profile card for a single person (Director, Principal, HOD, Dean, "
            "faculty member, staff member, student, or alumnus) or a single facility "
            "(a specific lab, canteen, library). "
            "NOT for lists of people or facilities — use show_faculty_grid or show_list."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "designation": {"type": "string"},
                "initials": {
                    "type": "string",
                    "description": "REQUIRED. 2-3 chars. Used when image unavailable."
                },
                "image_url": {
                    "type": "string",
                    "description": "Optional. Relative path served from Vercel CDN."
                },
                "details": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "icon": {
                                "type": "string",
                                "description": "Tabler icon name e.g. ti-mail, ti-phone, ti-award"
                            },
                            "label": {"type": "string"},
                            "value": {"type": "string"}
                        },
                        "required": ["icon", "label", "value"]
                    }
                }
            },
            "required": ["name", "designation", "initials", "details"]
        }
    },
    {
        "name": "show_faculty_grid",
        "description": (
            "Display a grid of faculty cards for a department. "
            "Use when student asks about all faculty in a specific department."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "department": {
                    "type": "string",
                    "description": "Full department name e.g. Computer Science & Engineering"
                },
                "members": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "initials": {
                                "type": "string",
                                "description": "REQUIRED. 2 chars. Used when image unavailable."
                            },
                            "designation": {"type": "string"},
                            "specialization": {"type": "string"},
                            "experience": {"type": "string"},
                            "image_url": {"type": "string"}
                        },
                        "required": ["name", "initials", "designation"]
                    }
                }
            },
            "required": ["department", "members"]
        }
    },
    {
        "name": "show_comparison",
        "description": (
            "Display a side-by-side numeric comparison. Use ONLY for numeric data: "
            "fee comparison between departments, intake seat counts by department. "
            "NEVER use for labs, facilities, predictions, or non-numeric lists."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "label": {"type": "string", "description": "e.g. department name"},
                            "value": {"type": "string", "description": "The numeric value e.g. '₹1,25,000'"},
                            "sublabel": {"type": "string", "description": "Optional sub-label"}
                        },
                        "required": ["label", "value"]
                    }
                }
            },
            "required": ["title", "items"]
        }
    },
    {
        "name": "show_list",
        "description": (
            "Display a list of items with descriptions. Use for: labs, facilities, "
            "clubs, bus routes, hostel facilities, placements by school/department, "
            "training programmes by category, scholarships by type, "
            "and any multi-category or multi-item non-numeric list "
            "where each item has a name + description. May include images."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "description": {"type": "string"},
                            "image_url": {"type": "string"},
                            "location": {"type": "string"},
                            "badge": {"type": "string", "description": "Optional badge text e.g. 'Block A'"},
                            "initials": {
                                "type": "string",
                                "description": "Optional. Used as image fallback."
                            }
                        },
                        "required": ["name", "description"]
                    }
                }
            },
            "required": ["title", "items"]
        }
    },
    {
        "name": "show_steps",
        "description": (
            "Display a numbered step-by-step process. Use for: admission process, "
            "how to apply, how to get a document, how to register on portal."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "steps": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "description": "Short step title"},
                            "detail": {"type": "string", "description": "Full step description"}
                        },
                        "required": ["title", "detail"]
                    }
                }
            },
            "required": ["title", "steps"]
        }
    },
    {
        "name": "show_contact",
        "description": (
            "Display contact information for escalation. Use when: student needs to "
            "speak to someone, has a problem the bot cannot solve, asks for contact details, "
            "or when no data is available for their query."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "reason": {
                    "type": "string",
                    "description": "Brief explanation of why escalation is needed"
                },
                "contacts": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "label": {"type": "string"},
                            "phone": {"type": "string"},
                            "email": {"type": "string"},
                            "hours": {"type": "string"},
                            "whatsapp": {"type": "string"}
                        },
                        "required": ["label"]
                    }
                }
            },
            "required": ["reason", "contacts"]
        }
    }
]