# backend/kb/vector_store.py
"""
AIKTC In-Memory Vector Store & Semantic Retrieval Engine
========================================================
Implements genuine vector-space embedding, cosine similarity calculation,
and top-k nearest neighbor retrieval for RAG.
"""

import re
import math
import logging
from collections import Counter
from typing import Any
from .chunker import TextChunk

logger = logging.getLogger("aiktc.vector_store")

STOPWORDS = {
    "a", "an", "the", "and", "or", "in", "on", "at", "to", "for", "with",
    "by", "of", "is", "are", "was", "were", "be", "been", "have", "has",
    "had", "do", "does", "did", "can", "could", "will", "would", "shall",
    "should", "may", "might", "must", "it", "its", "that", "this", "these",
    "those", "what", "which", "who", "whom", "where", "when", "why", "how",
    "hai", "kya", "ka", "ki", "ke", "ko", "se", "mein", "pe", "karo", "karna",
    # Domain & conversational query filler words
    "aiktc", "college", "campus", "institute", "tell", "show", "give", "me",
    "please", "about", "detail", "details", "info", "information", "want", "know"
}


DEPT_CANONICAL_MAP = {
    "CSE": {"CSE", "COMP", "CO"},
    "COMP": {"CSE", "COMP", "CO"},
    "CO": {"CSE", "COMP", "CO"},
    "IT": {"IT", "INFT", "BSIT", "BSCIT"},
    "BSIT": {"IT", "INFT", "BSIT", "BSCIT"},
    "BSCIT": {"IT", "INFT", "BSIT", "BSCIT"},
    "ECS": {"ECS", "EXTC", "ETRX"},
    "ECE": {"ECE"},
    "MECH": {"MECH"},
    "CIVIL": {"CIVIL"},
    "CHEM": {"CHEM"},
    "CSDS": {"CSDS", "DS", "DATA_SCIENCE"},
    "AIML": {"AIML", "CSAIML", "AI"},
    "CSAIML": {"AIML", "CSAIML", "AI"},
    "BPHARM": {"BPHARM"},
    "DPHARM": {"DPHARM"},
    "MPHARM": {"MPHARM"},
    "BARCH": {"BARCH"},
    "DARCH": {"DARCH"}
}

DEPT_SCHOOL_MAP = {
    "CSE": "engineering", "COMP": "engineering", "CO": "engineering",
    "IT": "engineering", "INFT": "engineering", "BSIT": "engineering", "BSCIT": "engineering",
    "ECS": "engineering", "EXTC": "engineering", "ETRX": "engineering",
    "ECE": "engineering",
    "MECH": "engineering", "CIVIL": "engineering", "CHEM": "engineering",
    "CSDS": "engineering", "DS": "engineering", "DATA_SCIENCE": "engineering",
    "AIML": "engineering", "CSAIML": "engineering", "AI": "engineering",
    "BPHARM": "pharmacy", "DPHARM": "pharmacy", "MPHARM": "pharmacy", "PHARMACY": "pharmacy",
    "BARCH": "architecture", "DARCH": "architecture", "ARCHITECTURE": "architecture"
}

def tokenize(text: str) -> list[str]:
    """Tokenize, stem common inflections, and filter stopwords for vector generation."""
    t_clean = text.lower()
    # Normalize Devanagari / Hindi / Marathi terms to English concepts for cross-lingual vector matching
    dev_map = {
        "कम्प्यूटर": "computer cse comp", "कंप्यूटर": "computer cse comp",
        "इंजीनियरिंग": "engineering", "अभियांत्रिकी": "engineering",
        "फीस": "fee tuition", "शुल्क": "fee tuition", "फी": "fee tuition",
        "दाखिला": "admission cap", "प्रवेश": "admission cap", "पात्रता": "eligibility",
        "छात्रवृत्ति": "scholarship", "शिष्यवृत्ती": "scholarship",
        "छात्रावास": "hostel", "वसतिगृह": "hostel",
        "प्लेसमेंट": "placement package", "नौकरी": "placement",
        "प्रयोगशाला": "lab", "सुविधाएं": "facilities", "सुविधा": "facilities",
        "फार्मेसी": "pharmacy bpharm", "औषधनिर्माण": "pharmacy",
        "आर्किटेक्चर": "architecture barch", "वास्तुशास्त्र": "architecture",
        "कटऑफ": "cutoff", "कैंटीन": "canteen food", "कॅन्टीन": "canteen food", "मेस": "mess food hostel",
        "जेवण": "canteen food", "जेवणाची": "canteen food", "सोय": "facilities",
        "पुस्तकालय": "library", "ग्रंथालय": "library"
    }
    for dev_word, eng_word in dev_map.items():
        if dev_word in t_clean:
            t_clean += f" {eng_word}"

    # Normalize common department aliases for consistent lexical matching
    if "computer science" in t_clean or "computer engg" in t_clean or "computer engineering" in t_clean:
        t_clean += " cse comp co"
    if "data science" in t_clean:
        t_clean += " csds ds"
    if "artificial intelligence" in t_clean or "machine learning" in t_clean:
        t_clean += " aiml ai"
    if "extc" in t_clean or "telecom" in t_clean or "electronics" in t_clean:
        t_clean += " ecs"

    tokens = re.findall(r'[a-zA-Z0-9_\u0900-\u097f]+', t_clean)
    normalized: list[str] = []
    for t in tokens:
        if t in STOPWORDS or len(t) <= 1:
            continue
        # Stem common plural / inflected forms
        if t in ("fees", "feez"):
            normalized.append("fee")
        elif t in ("labs", "laboratories"):
            normalized.append("lab")
        elif t in ("courses", "cours"):
            normalized.append("course")
        elif t in ("departments", "depts"):
            normalized.append("department")
        elif t in ("faculties", "professors", "teachers"):
            normalized.append("faculty")
        elif t in ("hostels",):
            normalized.append("hostel")
        elif t in ("placements", "packages"):
            normalized.append("placement")
        elif t in ("scholarships",):
            normalized.append("scholarship")
        elif t in ("cutoffs",):
            normalized.append("cutoff")
        elif t in ("admissions",):
            normalized.append("admission")
        elif t in ("enginerring", "engineering", "engg"):
            normalized.append("engineering")
        elif t in ("offere", "offers", "offered"):
            normalized.append("offer")
        elif t in ("programs", "programmes", "programme", "programm"):
            normalized.append("program")
        elif t in ("branches",):
            normalized.append("branch")
        elif t in ("degrees",):
            normalized.append("degree")
        elif t.endswith("s") and len(t) > 4 and not t.endswith(("ss", "us", "is")):
            normalized.append(t[:-1])
        else:
            normalized.append(t)
    return normalized


class VectorStore:
    """
    In-memory vector store implementing cosine similarity retrieval.
    """

    def __init__(self):
        self.chunks: list[TextChunk] = []
        self.doc_vectors: list[dict[str, float]] = []
        self.idf: dict[str, float] = {}
        self.vocab: set[str] = set()

    def build_index(self, chunks: list[TextChunk]) -> None:
        """
        Builds the vector space index from a list of document chunks.
        Computes IDF and normalized TF-IDF document vectors.
        """
        self.chunks = chunks
        num_docs = len(chunks)
        if num_docs == 0:
            return

        # 1. Document frequency
        df: Counter[str] = Counter()
        tokenized_docs: list[list[str]] = []

        for chunk in chunks:
            # Index both title and content (giving title 2x weight)
            full_text = f"{chunk.title} {chunk.title} {chunk.content}"
            tokens = tokenize(full_text)
            tokenized_docs.append(tokens)
            unique_terms = set(tokens)
            df.update(unique_terms)

        # 2. Compute IDF with smoothing
        self.idf = {
            term: math.log(1.0 + (num_docs / (count + 1.0))) + 1.0
            for term, count in df.items()
        }
        self.vocab = set(self.idf.keys())

        # 3. Compute normalized TF-IDF vector for each document
        self.doc_vectors = []
        for tokens in tokenized_docs:
            vec = self._compute_normalized_vector(tokens)
            self.doc_vectors.append(vec)

        logger.info(f"Vector store indexed {num_docs} chunks. Vocabulary size: {len(self.vocab)} terms.")

    def _compute_normalized_vector(self, tokens: list[str]) -> dict[str, float]:
        """Compute L2-normalized sublinear TF-IDF vector."""
        if not tokens:
            return {}
        tf = Counter(tokens)
        vec: dict[str, float] = {}
        sq_sum = 0.0

        for term, count in tf.items():
            if term in self.idf:
                # Sublinear term frequency scaling: 1 + ln(tf)
                weight = (1.0 + math.log(count)) * self.idf[term]
                vec[term] = weight
                sq_sum += weight * weight

        # L2-normalization for cosine distance
        norm = math.sqrt(sq_sum)
        if norm > 0.0:
            return {term: val / norm for term, val in vec.items()}
        return {}

    def _cosine_similarity(self, q_vec: dict[str, float], doc_vec: dict[str, float]) -> float:
        """Dot product of two L2-normalized vectors equals cosine similarity."""
        if not q_vec or not doc_vec:
            return 0.0
        # Dot product on intersecting keys
        if len(q_vec) < len(doc_vec):
            return sum(val * doc_vec.get(term, 0.0) for term, val in q_vec.items())
        else:
            return sum(val * q_vec.get(term, 0.0) for term, val in doc_vec.items())

    def search(
        self,
        query: str,
        top_k: int = 3,
        category: str | None = None,
        entities: dict[str, Any] | None = None,
        min_score: float = 0.02
    ) -> list[tuple[TextChunk, float]]:
        """
        Retrieves the top-k most semantically relevant chunks for a query.
        
        Args:
            query: User's raw or preprocessed question.
            top_k: Number of chunks to retrieve.
            category: Optional intent/category to provide a relevance boost.
            entities: Optional extracted entities (departments, person_intent) for precision boosting.
            min_score: Minimum cosine similarity threshold.
            
        Returns:
            List of (TextChunk, similarity_score) sorted descending.
        """
        q_tokens = tokenize(query)
        if not q_tokens:
            return []

        # Prepare entity target departments, target schools, and person intent
        target_depts: set[str] = set()
        target_schools: set[str] = set()
        person_intent: str | None = None

        q_lower = query.lower()
        if any(k in q_lower for k in ("engineering", "engg", "btech", "b.tech", "mtech", "m.tech", "bsc", "b.sc")):
            target_schools.add("engineering")
        if any(k in q_lower for k in ("pharmacy", "pharm", "bpharm", "b.pharm", "dpharm", "d.pharm", "mpharm", "m.pharm")):
            target_schools.add("pharmacy")
        if any(k in q_lower for k in ("architecture", "arch", "barch", "b.arch", "darch", "d.arch")):
            target_schools.add("architecture")

        if entities:
            raw_depts = entities.get("departments", [])
            for d in raw_depts:
                d_str = str(d).upper()
                if d_str in ("ENGINEERING", "PHARMACY", "ARCHITECTURE"):
                    target_schools.add(d_str.lower())
                else:
                    target_depts.update(DEPT_CANONICAL_MAP.get(d_str, {d_str}))
                    if d_str in DEPT_SCHOOL_MAP:
                        target_schools.add(DEPT_SCHOOL_MAP[d_str])
            person_intent = entities.get("person_intent")

        q_vec = self._compute_normalized_vector(q_tokens)
        results: list[tuple[TextChunk, float]] = []

        for i, doc_vec in enumerate(self.doc_vectors):
            base_score = self._cosine_similarity(q_vec, doc_vec)
            chunk = self.chunks[i]

            # 1. Category boost: if intent matches chunk category, boost score by 80%
            score = base_score
            category_matched = False
            if category:
                if chunk.category == category:
                    score *= 1.8
                    category_matched = True
                elif category in ("admission_process", "cap") and chunk.category in ("admission_process", "cap"):
                    score *= 1.8
                    category_matched = True
                elif category in ("facilities", "labs") and chunk.category == "facilities":
                    score *= 1.8
                    category_matched = True

            # 2. Entity / Department & School metadata boost & isolation
            chunk_dept = str(chunk.metadata.get("dept", "")).upper()
            chunk_school = str(chunk.metadata.get("school", "")).lower()

            if target_depts:
                if chunk_dept and chunk_dept in target_depts:
                    score *= 3.0
                elif chunk_dept and chunk_dept not in target_depts:
                    score *= 0.3  # Isolate requested department from other departments

            if target_schools:
                if chunk_school and chunk_school in target_schools:
                    score *= 3.0
                elif chunk_school and chunk_school not in target_schools and chunk_school in ("engineering", "pharmacy", "architecture"):
                    score *= 0.3  # Isolate requested school from other schools

            # 3. Person Intent boost: boost for leadership queries
            if person_intent:
                if person_intent in ("director", "principal"):
                    if chunk.chunk_id == "inst_leadership":
                        score *= 5.0
                    elif "_faculty" in chunk.chunk_id or "_overview" in chunk.chunk_id:
                        score *= 0.1
                elif person_intent == "dean":
                    if "dean" in chunk.chunk_id:
                        score *= 5.0
                    elif "_faculty" in chunk.chunk_id or "_overview" in chunk.chunk_id:
                        score *= 0.1

            # 4. Fee Structure vs Refund Policy vs Hostel Disambiguation
            q_lower_clean = query.lower()
            is_refund_query = bool(re.search(r'\b(?:refund|cancellation|canceling|cancel|deduct|deduction)\b', q_lower_clean))
            is_hostel_query = bool(re.search(r'\b(?:hostel|hostels|mess|accommodation|rooms?|stay)\b', q_lower_clean))
            is_fee_query = category == "fee" or bool(re.search(r'\b(?:fees?|cost|tuition|shulk|feestructure|फीस|शुल्क|फी|charges)\b', q_lower_clean))

            if is_hostel_query:
                if chunk.chunk_id == "inst_hostel":
                    score *= 3.0
                elif "_fees" in chunk.chunk_id:
                    score *= 0.2
            elif is_refund_query:
                if "refund" in chunk.chunk_id:
                    score *= 3.0
                elif "_fees" in chunk.chunk_id:
                    score *= 0.2
            elif is_fee_query:
                if "_fees" in chunk.chunk_id:
                    score *= 5.0
                    has_engg = "engineering" in target_schools or any(d in target_depts for d in ("CSE", "COMP", "CO", "IT", "BSIT", "BSCIT", "ECS", "EXTC", "ETRX", "ECE", "MECH", "CIVIL", "CHEM", "CSDS", "DS", "AIML", "CSAIML", "AI")) or any(k in q_lower_clean for k in ("eng", "btech", "mtech", "phd", "bsc", "b.tech", "m.tech", "b.sc"))
                    has_pharm = "pharmacy" in target_schools or any(d in target_depts for d in ("BPHARM", "DPHARM", "MPHARM")) or any(k in q_lower_clean for k in ("pharm", "bpharm", "dpharm", "mpharm", "b.pharm", "d.pharm", "m.pharm"))
                    has_arch = "architecture" in target_schools or any(d in target_depts for d in ("BARCH", "DARCH")) or any(k in q_lower_clean for k in ("arch", "barch", "darch", "b.arch", "d.arch"))

                    if has_engg and chunk.chunk_id == "engineering_fees":
                        score *= 4.0
                    elif has_engg and chunk.chunk_id in ("pharmacy_fees", "architecture_fees"):
                        score *= 0.1
                    elif has_pharm and chunk.chunk_id == "pharmacy_fees":
                        score *= 4.0
                    elif has_pharm and chunk.chunk_id in ("engineering_fees", "architecture_fees"):
                        score *= 0.1
                    elif has_arch and chunk.chunk_id == "architecture_fees":
                        score *= 4.0
                    elif has_arch and chunk.chunk_id in ("engineering_fees", "pharmacy_fees"):
                        score *= 0.1
                else:
                    score *= 0.1
            else:
                if "refund" in chunk.chunk_id:
                    score *= 0.2
                elif "_fees" in chunk.chunk_id:
                    score *= 0.2

            # 5. Faculty vs Laboratories / Facilities Disambiguation
            is_faculty_query = bool(re.search(r'\b(?:faculty|faculties|prof|professor|professors|teacher|teachers|teaches|teach|teaching|staff|hod|head|dean|director|principal|sir|madam|dr)\b', q_lower_clean))
            is_lab_query = bool(re.search(r'\b(?:lab|labs|laboratory|laboratories|equipment|machines?|hardware|specs?|facilities|facility)\b', q_lower_clean))

            if is_faculty_query:
                if "_faculty" in chunk.chunk_id or chunk.chunk_id == "inst_leadership" or "dean" in chunk.chunk_id:
                    score *= 3.0
                elif "_labs" in chunk.chunk_id:
                    score *= 0.2
                elif "_overview" in chunk.chunk_id:
                    score *= 0.2
            elif is_lab_query:
                if "_labs" in chunk.chunk_id:
                    score *= 4.0
                elif "_faculty" in chunk.chunk_id:
                    score *= 0.2
                elif "_overview" in chunk.chunk_id:
                    score *= 0.1
                elif "_programs_courses" in chunk.chunk_id:
                    score *= 0.1

            # 5b. Placements & Recruiters Disambiguation
            is_placement_query = (
                category == "placement"
                or bool(re.search(r'\b(?:placements?|package|highest package|average package|recruiters?|recruiting|companies|company|internships?|placed|tpo cell|tpo)\b', q_lower_clean))
            )
            if is_placement_query:
                if chunk.chunk_id == "campus_placements":
                    score *= 8.0
                elif "_faculty" in chunk.chunk_id or "_labs" in chunk.chunk_id or "_overview" in chunk.chunk_id:
                    score *= 0.1
                elif "incubation" in chunk.chunk_id:
                    score *= 0.1

            # 6. Scholarships Disambiguation (General vs Specific Categories vs Documents/Process)
            is_scholarship_query = category == "scholarship" or bool(re.search(r'\b(?:scholarships?|mahadbt|ebc|freeship)\b', q_lower_clean))
            if is_scholarship_query:
                if "scholarship" not in chunk.chunk_id:
                    score *= 0.1
                else:
                    is_doc_query = bool(re.search(r'\b(?:documents?|docs?|certificate|papers?|proof|income limit)\b', q_lower_clean))
                    is_apply_query = bool(re.search(r'\b(?:how to apply|apply for scholarship|application process|steps to apply)\b', q_lower_clean))
                    has_mahadbt = bool(re.search(r'\b(?:mahadbt|maha dbt|government scholarship portal|government portal)\b', q_lower_clean)) and not bool(re.search(r'\b(?:how to apply|steps to apply)\b', q_lower_clean))
                    is_contact_query = bool(re.search(r'\b(?:contact|desk|helpline|verification|incharge)\b', q_lower_clean))
                    has_obc = bool(re.search(r'\b(?:obc|ebc)\b', q_lower_clean))
                    has_sc_st = bool(re.search(r'\b(?:sc|st|caste)\b', q_lower_clean))
                    has_minority = bool(re.search(r'\b(?:minority|muslim)\b', q_lower_clean))
                    has_merit = bool(re.search(r'\b(?:merit|topper)\b', q_lower_clean))

                    if has_mahadbt:
                        score *= 6.0 if chunk.chunk_id == "scholarship_mahadbt" else 0.2
                    elif has_obc:
                        score *= 5.0 if chunk.chunk_id == "scholarship_obc" else 0.2
                    elif has_sc_st:
                        score *= 5.0 if chunk.chunk_id == "scholarship_sc_st" else 0.2
                    elif has_minority:
                        score *= 5.0 if chunk.chunk_id == "scholarship_minority" else 0.2
                    elif has_merit:
                        score *= 5.0 if chunk.chunk_id == "scholarship_merit" else 0.2
                    elif is_contact_query:
                        score *= 5.0 if chunk.chunk_id == "scholarship_contacts" else 0.2
                    elif is_doc_query:
                        score *= 5.0 if chunk.chunk_id == "scholarship_documents" else 0.2
                    elif is_apply_query:
                        score *= 5.0 if chunk.chunk_id == "scholarship_application_process" else 0.2
                    else:
                        score *= 4.0 if chunk.chunk_id == "scholarship_overview" else 0.3

            # 7. Central Facilities Disambiguation (Library, Incubation, Activities, Canteen)
            if re.search(r'\b(?:canteen|cafeteria|food|dining|snacks|lunch|breakfast|tea|coffee|refreshment|meals?|beverages?|कैंटीन|खाना|भोजन)\b', q_lower_clean):
                if is_hostel_query or "hostel" in q_lower_clean:
                    if chunk.chunk_id == "inst_hostel":
                        score *= 5.0
                else:
                    if chunk.chunk_id == "inst_canteen":
                        score *= 5.0
                    elif chunk.chunk_id == "inst_hostel":
                        score *= 2.0
            if re.search(r'\b(?:library|books?|reading room|krrc|journals?)\b', q_lower_clean):
                if chunk.chunk_id == "engineering_library":
                    score *= 4.0
            if re.search(r'\b(?:incubation|innovation|startup|entrepreneur|edc)\b', q_lower_clean) and not is_placement_query:
                if chunk.chunk_id == "engineering_incubation":
                    score *= 4.0
            if re.search(r'\b(?:clubs?|activities|activity|events?|fests?|festival|ieee|csi|cultural|sports|bonhomie|fuerza|tournaments?|hackathons?|nexathon|algorithm|competitions?)\b', q_lower_clean):
                if chunk.chunk_id == "campus_activities":
                    score *= 10.0
                elif "_faculty" in chunk.chunk_id or "_overview" in chunk.chunk_id or "_labs" in chunk.chunk_id or "_fees" in chunk.chunk_id:
                    score *= 0.1

            # 8. Contact vs Overview Disambiguation
            if re.search(r'\b(?:contact|phone|telephone|email|mail|call|reach|address|location|map)\b', q_lower_clean):
                if chunk.chunk_id == "inst_contact":
                    score *= 2.5
            if re.search(r'\b(?:about|overview|history|established|affiliation|approved|dte code)\b', q_lower_clean):
                if chunk.chunk_id == "inst_overview":
                    score *= 2.5

            # 9. Admission Eligibility vs CAP Application Process vs Cutoffs
            is_cutoff_search = bool(re.search(r'\b(?:cutoff|cut off|cut-off|percentile|closing rank|closing score)\b', q_lower_clean))
            is_elig_search = bool(re.search(r'\b(?:eligibility|eligible|criteria|percentage required|minimum marks|qualification|requirements?|score requirement|pcm percentage|pcm)\b', q_lower_clean))
            is_cap_search = bool(re.search(r'\b(?:cet cell|cap round|cap|option form|seat allotment|reporting center|arc|institutional round|vacant seat|admission process|steps to register|register on cet)\b', q_lower_clean)) or category == "cap"

            if is_cutoff_search:
                if "_faculty" in chunk.chunk_id or "_labs" in chunk.chunk_id:
                    score *= 0.1
                elif chunk.chunk_id == "cap_admission_process":
                    score *= 2.5
                elif "_admission_eligibility" in chunk.chunk_id:
                    score *= 2.0
            elif is_cap_search and not is_elig_search and not is_scholarship_query:
                if chunk.chunk_id == "cap_admission_process":
                    score *= 5.0
                elif "scholarship" in chunk.chunk_id or "_faculty" in chunk.chunk_id:
                    score *= 0.1
            elif is_elig_search:
                if "_faculty" in chunk.chunk_id or "_labs" in chunk.chunk_id or "_overview" in chunk.chunk_id:
                    score *= 0.1
                elif "_admission_eligibility" in chunk.chunk_id:
                    score *= 3.0
                    if any(k in q_lower_clean for k in ("pharm", "bpharm", "dpharm")):
                        score *= 3.0 if chunk.chunk_id == "pharmacy_admission_eligibility" else 0.1
                    elif any(k in q_lower_clean for k in ("arch", "barch", "darch", "nata")):
                        score *= 3.0 if chunk.chunk_id == "architecture_admission_eligibility" else 0.1
                    elif any(k in q_lower_clean for k in ("eng", "btech", "mtech", "pcm", "mht cet", "direct second")):
                        score *= 3.0 if chunk.chunk_id == "engineering_admission_eligibility" else 0.1

            # 10. Courses, Degrees, Programs & Branches Disambiguation
            is_course_query = (
                category == "courses_offered"
                or bool(re.search(r'\b(?:courses?|programmes?|programs?|degrees?|branches?|specializations?)\b', q_lower_clean))
                or bool(re.search(r'\b(?:what does aiktc offer|what course|which course|what are available course|what courses|courses offered|programs offered)\b', q_lower_clean))
            ) and not is_fee_query
            if is_course_query:
                if "_labs" in chunk.chunk_id or "_faculty" in chunk.chunk_id:
                    score *= 0.05
                elif "scholarship" in chunk.chunk_id:
                    score *= 0.05
                elif "_programs_courses" in chunk.chunk_id or chunk.chunk_id == "inst_programs_courses":
                    score *= 4.0
                    if any(k in q_lower_clean for k in ("eng", "enginerring", "btech", "b.tech")):
                        if chunk.chunk_id == "engineering_programs_courses":
                            score *= 3.0
                    elif any(k in q_lower_clean for k in ("pharm", "bpharm", "dpharm")):
                        if chunk.chunk_id == "pharmacy_programs_courses":
                            score *= 3.0
                    elif any(k in q_lower_clean for k in ("arch", "barch", "darch")):
                        if chunk.chunk_id == "architecture_programs_courses":
                            score *= 3.0
                    else:
                        if chunk.chunk_id == "inst_programs_courses":
                            score *= 3.0

            # 11. Department Comparisons & Department Overviews
            is_comparison_query = (
                category == "compare_departments"
                or bool(re.search(r'\b(?:difference|differ|diff|compare|comparison|versus|vs\.?|distinguish|which is better|choose between|prefer)\b', q_lower_clean))
                or (entities and len(entities.get("departments", [])) >= 2)
            )
            is_dept_overview = (
                category == "department_overview"
                or (
                    bool(re.search(r'\b(?:about|tell me about|describe|overview|scope|details of|introduction to|information about|what is|curriculum of)\b', q_lower_clean))
                    and not is_faculty_query
                    and not is_lab_query
                    and not is_course_query
                    and not is_fee_query
                    and not is_placement_query
                )
            )

            if is_comparison_query:
                if "_overview" in chunk.chunk_id:
                    score *= 5.0
                elif "_programs_courses" in chunk.chunk_id:
                    score *= 2.0
                elif "_faculty" in chunk.chunk_id:
                    score *= 0.2
                elif "_labs" in chunk.chunk_id:
                    score *= 0.2
            elif is_dept_overview and target_depts:
                if "_overview" in chunk.chunk_id:
                    score *= 4.0
                elif "_faculty" in chunk.chunk_id:
                    score *= 0.3
                elif "_labs" in chunk.chunk_id:
                    score *= 0.3

            if score >= min_score:
                results.append((chunk, score))

        # Sort descending by similarity score
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]
