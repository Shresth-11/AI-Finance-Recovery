import re

def normalize_text(text: str) -> str:
    if not text:
        return ""
    cleaned = text.strip().lower()
    cleaned = re.sub(r"[^\w\s]", " ", cleaned)
    # Replace common business entity abbreviations
    replacements = {
        "pvt": "private",
        "ltd": "limited",
        "softwares": "software",
        "corp": "corporation",
        "inc": "incorporated"
    }
    words = cleaned.split()
    normalized_words = [replacements.get(w, w) for w in words]
    return " ".join(normalized_words)

def normalize_email(email: str) -> str:
    if not email:
        return ""
    return email.strip().lower()

def normalize_amount(amount: float) -> float:
    if amount is None:
        return 0.0
    return round(float(amount), 2)

def normalize_reference_id(ref_id: str) -> str:
    if not ref_id:
        return ""
    # Strip spaces, hyphens, underscores and uppercase
    cleaned = re.sub(r"[\s\-_]", "", ref_id.strip()).upper()
    return cleaned
