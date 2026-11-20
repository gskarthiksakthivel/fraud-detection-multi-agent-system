# Threat Model — Fraud Agentic AI

## Threat Vectors & Mitigations

| Threat | Attack Vector | Mitigation | Status |
|---|---|---|---|
| Prompt injection | Malicious merchant name or transaction description | `detect_prompt_injection()` in safety.py | ✅ Implemented |
| PII leakage to LLM | IBAN/BSN/card numbers in transaction data | `redact_pii()` before every LLM call | ✅ Implemented |
| Data exfiltration via LLM | Agent prompted to return sensitive data | Output validation + audit logging | ✅ Implemented |
| Token flooding | Attacker submits huge payloads | Rate limiting + input length validation | ✅ Implemented |
| JWT replay attack | Stolen token reused | Short JWT expiry (60 min) + stateless validation | ✅ Implemented |
| MCP server spoofing | Attacker stands up fake MCP server | Server URLs in config only, not user input | ✅ Implemented |
| Redis session poisoning | Attacker injects malicious session state | Sessions are write-once, never user-controlled | ✅ Implemented |
| LLM hallucinated decisions | LLM invents fraud evidence | Structured output + confidence thresholds + audit | ✅ Implemented |
| GDPR data breach | Personal data retained beyond retention period | Audit log TTL policy + PII redaction | ✅ Implemented |

## GDPR Compliance

- Legal basis: Article 6(1)(f) — Legitimate interest (fraud prevention)
- Data minimisation: only transaction metadata processed, not full personal data
- PII redacted before LLM processing
- Every data access logged in `gdpr_audit_log` via Compliance MCP
- Retention: 7 years for financial records (Dutch law requirement)
- Data processor records maintained per Article 30

## PCI-DSS Relevant Controls

- Card numbers redacted via `pii_patterns.py` before any LLM call
- No card data stored in Redis or ChromaDB
- Audit trail for every transaction decision
- Human-in-the-loop approval gates for auto-block decisions
- JWT authentication on all API endpoints
