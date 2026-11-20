"""
pii_patterns.py
===============
LAYER: Security — PII Patterns Registry

Central registry of PII regex patterns.
Used by guardrails/safety.py and audit_logger.py.
Add new patterns here — they apply everywhere automatically.
"""

# PII patterns: name → regex
PII_PATTERNS = {
    "iban": r"\b[A-Z]{2}\d{2}[A-Z0-9]{4,30}\b",
    "bsn": r"\b\d{9}\b",                          # Dutch BSN
    "card_number": r"\b(?:\d{4}[-\s]?){3}\d{4}\b",
    "email": r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b",
    "phone_nl": r"\b(?:\+31|0031|0)\s*[-]?\s*(?:\d\s*){9}\b",
    "phone_international": r"\b\+\d{1,3}[\s\-]?\(?\d{1,4}\)?[\s\-]?\d{3,4}[\s\-]?\d{3,4}\b",
    "ip_address": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
    "passport": r"\b[A-Z]{1,2}\d{6,9}\b",
}

# Prompt injection detection patterns
INJECTION_PATTERNS = [
    r"ignore (previous|all|your) instructions?",
    r"you are now",
    r"forget (your|the) (system|previous) (prompt|instructions?)",
    r"disregard (the|your|all) (above|previous|system)",
    r"act as (a|an|if)",
    r"new instructions?:",
    r"override (mode|system)",
    r"jailbreak",
    r"dan mode",
    r"do anything now",
    r"pretend (you are|to be)",
]
