# backend/prompt/extraction.py

CUTOFF_EXTRACTION_PROMPT = """
You are a precise data extractor. Given the following raw text from a cutoff notice, extract all cutoff entries for MHT-CET percentile or NATA marks.

Output a JSON object with a key "cutoffs" containing an array of objects. Each object must have:
- "school": one of "engineering", "pharmacy", "architecture" (infer from department names)
- "branch": the department code (use: CSE, IT, ECS, MECH, CIVIL, BPHARM, MPHARM, BARCH)
- "category": one of "Open", "OBC", "SC", "ST", "EWS", "TFWS"
- "year": the year as an integer
- "cutoff": the cutoff number as a float (for percentile it's 0-100, for marks usually 0-200)
- "cutoff_unit": "percentile" or "marks"

If the text mentions "percentile", use "percentile". If it mentions "NATA" or "marks out of 200", use "marks". For any ambiguous department name, use your best guess from the context but do NOT invent data.

Raw text:
{raw_text}

JSON output (strictly valid JSON with no markdown formatting):
"""

FACULTY_EXTRACTION_PROMPT = """
You are a precise data extractor. Given the following raw text, extract the list of faculty members.

Output a JSON object with a key "faculty" containing an array of objects. Each object must have:
- "name": string
- "designation": string (e.g. "Assistant Professor", "HOD", "Professor")
- "specialization": string
- "email": string (if available, otherwise empty string)
- "experience_years": number (if available, otherwise null)

Raw text:
{raw_text}

JSON output (strictly valid JSON with no markdown formatting):
"""

COMMON_EXTRACTION_PROMPT = """
You are a precise data extractor. Given the following raw text, extract key contacts and common information.

Output a JSON object representing the contact info. It should have the following structure based on the text provided:
- "director": {"name": "", "email": ""}
- "principal": {"name": "", "email": ""}
- "admissions_contact": {"phone": "", "email": ""}
- "general_contact": {"phone": "", "email": ""}

Raw text:
{raw_text}

JSON output (strictly valid JSON with no markdown formatting):
"""
