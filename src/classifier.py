import re
from dataclasses import dataclass
from typing import List, Optional

from model_adapter import moderate

@dataclass
class Classification:
    category: str
    severity: str
    reasons: List[str]

BYPASS_TERMS = [
    "ignore previous", "ignore the rules", "disable parental", "turn off parental",
    "pretend i am 18", "pretend i am 21", "jailbreak", "developer mode",
    "hide from my parents", "bypass", "uncensored", "encode your answer"
]

SELF_HARM_TERMS = ["kill myself", "suicide", "self harm", "hurt myself", "end my life"]
EATING_TERMS = ["starve", "purge", "lose weight fast", "not eating", "thinspo"]
SEXUAL_TERMS = ["porn", "explicit sex", "nudes", "sexting"]
DRUG_TERMS = ["drugs", "drug", "cocaine", "heroin", "weed", "meth", "get high", "make drugs"]
WEAPON_TERMS = ["make a bomb", "build a gun", "knife attack", "weapon instructions"]
VIOLENCE_TERMS = ["torture", "graphic violence", "how to hurt", "how to fight"]
GAMBLING_TERMS = ["online casino", "sports betting", "gambling trick"]

INSTRUCTIONAL_HINTS = ["how to make", "steps to", "instructions", "recipe", "hide", "avoid getting caught"]

# These terms no longer decide severity on their own for the categories OpenAI
# moderation covers — they just mark a topic as sensitive enough to guarantee at
# least a REWRITE, even when the raw text itself scores as harmless (e.g. "what
# are drugs, we're learning about them in school"). Actual severity for those
# categories comes from the moderation score below.
TOPIC_TERMS = {
    "self_harm": SELF_HARM_TERMS,
    "sexual": SEXUAL_TERMS,
    "drugs": DRUG_TERMS,
    "weapons": WEAPON_TERMS,
    "violence": VIOLENCE_TERMS,
}

# OpenAI's moderation taxonomy has no dedicated "drugs" or "weapons" category;
# "illicit" (non-violent wrongdoing) and "illicit_violent" are the closest proxies.
MODERATION_CATEGORY_MAP = {
    "self_harm": ["self_harm", "self_harm_intent", "self_harm_instructions"],
    "sexual": ["sexual", "sexual_minors"],
    "drugs": ["illicit"],
    "weapons": ["illicit_violent"],
    "violence": ["violence", "violence_graphic"],
}

# Category-specific flags that always mean "high severity", regardless of score.
FORCED_HIGH_FLAGS = {
    "self_harm": ["self_harm_intent", "self_harm_instructions"],
    "sexual": ["sexual_minors"],
}

# Lower bars for younger children: a smaller moderation score is enough to act on.
AGE_BAND_THRESHOLDS = {
    "8-10": {"medium": 0.05, "high": 0.3},
    "11-13": {"medium": 0.10, "high": 0.5},
    "14-16": {"medium": 0.15, "high": 0.7},
}
DEFAULT_AGE_BAND = "11-13"


def _contains(text: str, terms: List[str]) -> List[str]:
    low = text.lower()
    # Word-boundary match so short terms like "meth" don't fire inside
    # unrelated words like "method".
    return [term for term in terms if re.search(rf"\b{re.escape(term)}\b", low)]


def _moderation_signal(moderation: Optional[dict], category: str) -> tuple:
    if moderation is None:
        return 0.0, False
    keys = MODERATION_CATEGORY_MAP[category]
    score = max(moderation["scores"].get(k, 0.0) for k in keys)
    forced_high = any(moderation["categories"].get(k) for k in FORCED_HIGH_FLAGS.get(category, []))
    return score, forced_high


def classify(text: str, age_band: str = DEFAULT_AGE_BAND) -> Classification:
    low = text.lower()
    thresholds = AGE_BAND_THRESHOLDS.get(age_band, AGE_BAND_THRESHOLDS[DEFAULT_AGE_BAND])

    bypass = _contains(low, BYPASS_TERMS)
    if bypass:
        return Classification("bypass", "high", [f"Bypass/jailbreak term: {t}" for t in bypass])

    moderation = moderate(text)
    instructional = any(h in low for h in INSTRUCTIONAL_HINTS)

    signals = {}
    for category, terms in TOPIC_TERMS.items():
        hits = _contains(low, terms)
        score, forced_high = _moderation_signal(moderation, category)
        if hits or score >= thresholds["medium"]:
            signals[category] = (hits, score, forced_high)

    if signals:
        # OpenAI's categories overlap (e.g. "illicit" vs "illicit_violent" both
        # fire for bomb-making), so picking by score alone can pick the wrong
        # Milo category. A category a keyword list actually matched wins first;
        # only fall back to pure moderation score when nothing matched a term.
        with_hits = {c: v for c, v in signals.items() if v[0]}
        pool = with_hits or signals
        category = max(pool, key=lambda c: pool[c][1])
        hits, score, forced_high = signals[category]

        severity = "high" if (
            forced_high or score >= thresholds["high"]
            or category in {"self_harm", "weapons"} or instructional
        ) else "medium"

        reasons = [f"Sensitive topic term: {t}" for t in hits]
        if moderation is not None:
            reasons.append(f"OpenAI moderation: {category} score={score:.2f}")
        return Classification(category, severity, reasons)

    for category, terms in [("eating_disorder", EATING_TERMS), ("gambling", GAMBLING_TERMS)]:
        hits = _contains(low, terms)
        if hits:
            severity = "high" if instructional else "medium"
            return Classification(category, severity, [f"Sensitive term: {t}" for t in hits])

    return Classification("general", "low", ["No restricted category detected"])
