"""
safety.py
=========
LAYER: Guardrails — PII Redaction + Prompt Injection Defence

Two responsibilities:
1. PII redaction — strip IBAN, BSN, card numbers, email, phone from text
   before sending to LLM (GDPR requirement)
2. Prompt injection detection — reject inputs that attempt to override
   agent system prompts

Called by every agent before passing data to LLM.
"""

import re
import logging
from app.security.pii_patterns import PII_PATTERNS, INJECTION_PATTERNS

logger = logging.getLogger(__name__)


def redact_pii(text: str) -> str:
    """
    Redact all PII patterns from text.
    Returns redacted text safe to send to external LLM APIs.
    """
    if not text:
        return text

    redacted = text
    for pattern_name, pattern in PII_PATTERNS.items():
        matches = re.findall(pattern, redacted, re.IGNORECASE)
        if matches:
            logger.debug(f"[GUARDRAILS] Redacting {len(matches)} {pattern_name} instances")
        redacted = re.sub(pattern, f"[{pattern_name.upper()}_REDACTED]", redacted, flags=re.IGNORECASE)

    return redacted


def detect_prompt_injection(text: str) -> bool:
    """
    Detect prompt injection attempts in user input.
    Returns True if injection detected (caller should reject).

    Common attacks:
    - "Ignore previous instructions"
    - "You are now a different AI"
    - "Forget your system prompt"
    """
    if not text:
        return False

    text_lower = text.lower()
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text_lower):
            logger.warning(f"[GUARDRAILS] Prompt injection detected: pattern='{pattern}' input='{text[:100]}'")
            return True

    return False


def validate_input(text: str) -> tuple[bool, str]:
    """
    Validate input text — checks for injection and returns sanitised version.
    Returns (is_safe, sanitised_text).
    """
    if detect_prompt_injection(text):
        return False, ""

    sanitised = redact_pii(text)
    return True, sanitised


def sanitise_llm_output(output: str) -> str:
    """
    Sanitise LLM output before returning to caller.
    Removes any PII that might have leaked through, strips meta-instructions.
    """
    if not output:
        return output

    # Remove any leaked PII
    sanitised = redact_pii(output)

    # Remove common LLM meta-text
    meta_patterns = [
        r"As an AI language model,?\s*",
        r"I cannot assist with\s*",
        r"<\|.*?\|>",  # Token artifacts
    ]
    for pattern in meta_patterns:
        sanitised = re.sub(pattern, "", sanitised, flags=re.IGNORECASE)

    return sanitised.strip()
