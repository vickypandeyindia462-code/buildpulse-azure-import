from typing import Dict, Any, Optional, List
import asyncio
import re


EMAIL_RE = re.compile(r"[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}")
SSN_RE = re.compile(r"\b\d{3}-?\d{2}-?\d{4}\b")
SECRET_RE = re.compile(
    r"\b(?:gh[pousr]_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9_-]{20,})\b",
    re.IGNORECASE,
)


def scan_and_redact(text: str) -> Dict[str, Any]:
    patterns = (("EMAIL", EMAIL_RE), ("SSN", SSN_RE), ("SECRET", SECRET_RE))
    findings = []
    redacted = text
    for finding_type, pattern in patterns:
        matches = list(pattern.finditer(redacted))
        findings.extend({"type": finding_type, "start": match.start(), "end": match.end()} for match in matches)
        redacted = pattern.sub(f"[REDACTED_{finding_type}]", redacted)
    return {"redacted_text": redacted, "findings": findings}


async def run(text: str, context: Dict[str, Any], db=None, tools: Optional[Dict[str, Any]] = None):
    """Simple security PII check: find emails and SSN-like patterns."""

    def _scan(t):
        return scan_and_redact(t)

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, _scan, text)
    return {
        "text_snippet": result["redacted_text"][:200],
        "redacted_text": result["redacted_text"],
        "findings": result["findings"],
    }


def run_sync(text: str, context: Dict[str, Any], db=None):
    import asyncio

    return asyncio.run(run(text, context, db))
