import uuid
import hashlib
from datetime import datetime


def generate_id() -> str:
    return str(uuid.uuid4())


def generate_short_id() -> str:
    return uuid.uuid4().hex[:12]


def timestamp_now() -> str:
    return datetime.utcnow().isoformat()


def hash_content(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def truncate_text(text: str, max_length: int = 200) -> str:
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."


def clean_text(text: str) -> str:
    import re
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()
