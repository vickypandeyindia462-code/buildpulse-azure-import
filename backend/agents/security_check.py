from typing import Dict, Any, Optional, List
import asyncio
import re


EMAIL_RE = re.compile(r"[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}")
SSN_RE = re.compile(r"\b\d{3}-?\d{2}-?\d{4}\b")


async def run(text: str, context: Dict[str, Any], db=None, tools: Optional[Dict[str, Any]] = None):
    """Simple security PII check: find emails and SSN-like patterns."""

    def _scan(t):
        findings = []
        for m in EMAIL_RE.finditer(t):
            findings.append({"type": "EMAIL", "match": m.group(0)})
        for m in SSN_RE.finditer(t):
            findings.append({"type": "SSN", "match": m.group(0)})
        return findings

    loop = asyncio.get_event_loop()
    findings = await loop.run_in_executor(None, _scan, text)
    return {"text_snippet": text[:200], "findings": findings}


def run_sync(text: str, context: Dict[str, Any], db=None):
    import asyncio

    return asyncio.run(run(text, context, db))
