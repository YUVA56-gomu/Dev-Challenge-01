import re
from typing import Tuple, Dict, Optional

STATUTORY_PATTERNS = [
    r'\bsection\s*\d+',
    r'\bsec\s*\d+',
    r'\brule\s*\d+',
    r'\bas\s*\d+',
    r'\bsa\s*\d+',
    r'\bind\s*as\s*\d+',
    r'\bschedule\s*[i|v|x]+',
    r'\bcaro\b',
    r'\bgst\b',
    r'\bitc\b',
    r'\btds\b',
    r'\btcs\b',
    r'\bpgbp\b',
    r'\bdepreciation\b',
    r'\bblocked\s*credit',
    r'\bauditor\b',
    r'\bdisqualification',
    r'\bcasual\s*vacancy',
    r'\binherent\s*limitation',
    r'\breasonable\s*assurance',
    r'\bbalance\s*sheet\b',
    r'\bmaterial\s*misstatement',
    r'\bamalgamation\b',
    r'\baccounting\s*standard',
]

CASUAL_GREETINGS = [
    r'^(hi|hello|hey|namaste|good\s*(morning|afternoon|evening)|howdy)\b',
    r'^(how\s*are\s*you|who\s*are\s*you|what\s*is\s*your\s*name)\b',
    r'^(thanks|thank\s*you|bye|goodbye|see\s*you)\b',
    r'^(i\s*am\s*feeling|i\s*feel\s*(tired|stressed|overwhelmed|anxious|sad|demotivated))\b',
    r'^(help\s*me\s*calm\s*down|can\s*we\s*take\s*a\s*break)\b',
]

def route_query(query: str, active_context: Optional[Dict] = None) -> Tuple[str, Dict]:
    """
    Intelligently routes a user query to 'fast' path or 'deep' path.
    - Fast Path: Greetings, casual check-ins, emotional support, simple motivation.
    - Deep Path: Statutory sections, CA standards, syllabus queries, or explicit chapter context.
    """
    q_lower = query.strip().lower()

    # 1. If explicit chapter/topic study context is attached (e.g. from "Ask Sathi")
    if active_context and (active_context.get("chapter") or active_context.get("topic") or active_context.get("statutory_section")):
        return "deep", {
            "reason": "explicit_study_context",
            "context": active_context,
            "query": query,
        }

    # 2. Check for fast casual greetings / emotional check-ins
    for pattern in CASUAL_GREETINGS:
        if re.search(pattern, q_lower):
            return "fast", {
                "reason": "greeting_or_wellbeing",
                "matched_pattern": pattern,
            }

    # 3. Check for deep statutory & syllabus patterns
    for pattern in STATUTORY_PATTERNS:
        match = re.search(pattern, q_lower)
        if match:
            return "deep", {
                "reason": "statutory_keyword",
                "matched": match.group(0),
            }

    # 4. Check for typical academic inquiry words
    academic_keywords = [
        "explain", "what is", "how to calculate", "rule for", "limit for",
        "difference between", "provisions of", "penalty for", "due date",
        "appointment", "disqualification", "input tax credit", "exemption",
        "eligibility", "exam question", "quiz me", "mnemonic"
    ]
    for kw in academic_keywords:
        if kw in q_lower:
            return "deep", {
                "reason": "academic_inquiry",
                "keyword": kw,
            }

    # If short conversational remark without academic keywords
    if len(q_lower.split()) < 4 and not any(k in q_lower for k in ["ca", "tax", "audit", "law", "cost"]):
        return "fast", {
            "reason": "short_conversational",
        }

    # Default to deep path to ensure accurate grounded assistance
    return "deep", {
        "reason": "default_academic_safety",
    }
