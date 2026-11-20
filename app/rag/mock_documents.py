"""
mock_documents.py
=================
LAYER: RAG — Seed Data

20 mock fraud case documents used to seed ChromaDB.
Run scripts/seed_vector_db.py to load these into ChromaDB.
In production these come from the real case management system.
"""

MOCK_FRAUD_CASES = [
    {
        "case_id": "CASE-001",
        "summary": "Account ACC-789 made 8 transactions in 45 minutes totalling EUR 12,400 across crypto exchanges in Russia. Velocity abuse detected. Account frozen after third transaction. Confirmed fraud — stolen card used through Tor exit node.",
        "metadata": {"outcome": "CONFIRMED_FRAUD", "fraud_type": "velocity_abuse", "amount_range": "10000-25000", "country": "RU"}
    },
    {
        "case_id": "CASE-002",
        "summary": "Series of EUR 9,800 transactions to structuring typology — customer split payments to stay below EUR 10,000 reporting threshold. AML typology: structuring. SAR filed with FIU-NL. Account placed under enhanced monitoring.",
        "metadata": {"outcome": "SAR_FILED", "fraud_type": "structuring", "amount_range": "9000-10000", "country": "NL"}
    },
    {
        "case_id": "CASE-003",
        "summary": "Transaction flagged for geo-IP mismatch — account registered in Netherlands but IP address from Nigeria. Card-not-present fraud. KYC enhanced due diligence triggered. Transaction blocked. Reported as identity theft.",
        "metadata": {"outcome": "BLOCKED", "fraud_type": "geo_anomaly", "amount_range": "1000-5000", "country": "NG"}
    },
    {
        "case_id": "CASE-004",
        "summary": "OFAC sanctions list match on merchant CryptoExchange XYZ — entity linked to sanctioned jurisdiction. Transaction immediately blocked. Compliance team notified. SAR mandatory filing initiated.",
        "metadata": {"outcome": "SANCTIONS_BLOCK", "fraud_type": "sanctions_hit", "amount_range": "5000-50000", "country": "IR"}
    },
    {
        "case_id": "CASE-005",
        "summary": "Business account used for unusual consumer purchases — high-value electronics across 6 countries in 3 days. Device fingerprint mismatch on every transaction. Confirmed account takeover via phishing. All transactions reversed.",
        "metadata": {"outcome": "ACCOUNT_TAKEOVER", "fraud_type": "device_mismatch", "amount_range": "500-3000", "country": "CN"}
    },
    {
        "case_id": "CASE-006",
        "summary": "New account opened 3 days ago making EUR 45,000 transfer to offshore account. KYC basic tier only — enhanced due diligence not completed. Account frozen pending investigation. Suspected money mule.",
        "metadata": {"outcome": "UNDER_INVESTIGATION", "fraud_type": "money_mule", "amount_range": "25000-100000", "country": "CY"}
    },
    {
        "case_id": "CASE-007",
        "summary": "Legitimate customer incorrectly flagged for velocity abuse during holiday season shopping. 7 transactions across legitimate UK retailers. False positive — customer notified and transaction cleared within 2 hours.",
        "metadata": {"outcome": "FALSE_POSITIVE", "fraud_type": "velocity_abuse", "amount_range": "100-500", "country": "GB"}
    },
    {
        "case_id": "CASE-008",
        "summary": "Casino gambling transactions from account with PEP (Politically Exposed Person) designation. AML enhanced screening triggered. Source of funds requested. Account placed under monitoring per DNB requirements.",
        "metadata": {"outcome": "ENHANCED_MONITORING", "fraud_type": "pep_screening", "amount_range": "5000-20000", "country": "MT"}
    },
    {
        "case_id": "CASE-009",
        "summary": "Crypto exchange deposit of EUR 78,000 from account with clean history. Large transaction reporting threshold breached. Customer provided satisfactory source of funds documentation. Cleared after 48h review.",
        "metadata": {"outcome": "CLEARED", "fraud_type": "large_transaction", "amount_range": "50000-100000", "country": "NL"}
    },
    {
        "case_id": "CASE-010",
        "summary": "Phishing victim made EUR 3,200 payment to fraudulent IBAN disguised as utility company. Authorised push payment fraud. Bank of origin attempted clawback — partially recovered EUR 1,800. Customer reimbursed per DSP2.",
        "metadata": {"outcome": "APP_FRAUD", "fraud_type": "authorised_push_payment", "amount_range": "1000-5000", "country": "NL"}
    },
    {
        "case_id": "CASE-011",
        "summary": "Card skimming attack at ATM in Eastern Europe — cloned card used for EUR 2,400 cash withdrawal. Physical card still with customer. Device fingerprint completely different. Transaction reversed. New card issued.",
        "metadata": {"outcome": "CARD_FRAUD", "fraud_type": "card_skimming", "amount_range": "1000-5000", "country": "RO"}
    },
    {
        "case_id": "CASE-012",
        "summary": "Business email compromise — finance employee tricked into changing supplier IBAN. EUR 125,000 transferred to fraudster account in Hong Kong. Full investigation triggered. Partial recovery via swift recall.",
        "metadata": {"outcome": "BEC_FRAUD", "fraud_type": "business_email_compromise", "amount_range": "100000+", "country": "HK"}
    },
    {
        "case_id": "CASE-013",
        "summary": "Investment fraud — customer transferred EUR 18,000 to fake investment platform promising high crypto returns. Platform operated from Russia. Funds unrecoverable. Fraud reported to national police.",
        "metadata": {"outcome": "INVESTMENT_FRAUD", "fraud_type": "investment_scam", "amount_range": "10000-25000", "country": "RU"}
    },
    {
        "case_id": "CASE-014",
        "summary": "Money service business account processing unusually high volume of cash equivalent transactions. Pattern consistent with layering — funds from multiple sources consolidated then distributed. SAR filed.",
        "metadata": {"outcome": "SAR_FILED", "fraud_type": "layering", "amount_range": "50000-100000", "country": "NL"}
    },
    {
        "case_id": "CASE-015",
        "summary": "Student account receiving and immediately forwarding large sums — confirmed money mule recruited via social media job scam. Account closed. Customer referred for prosecution. Victim support provided.",
        "metadata": {"outcome": "MONEY_MULE_CONFIRMED", "fraud_type": "money_mule", "amount_range": "5000-20000", "country": "NL"}
    },
    {
        "case_id": "CASE-016",
        "summary": "High-value art transaction EUR 340,000 — legitimate but triggered AML review due to art market AMLD5 requirements. Customer is art dealer with verifiable business history. Cleared after enhanced due diligence.",
        "metadata": {"outcome": "CLEARED", "fraud_type": "large_transaction", "amount_range": "100000+", "country": "BE"}
    },
    {
        "case_id": "CASE-017",
        "summary": "Synthetic identity fraud — account opened with fabricated identity documents passing automated KYC. Used for 6 months before fraud pattern detected. EUR 8,400 in fraudulent purchases. Identity documents flagged in national database.",
        "metadata": {"outcome": "CONFIRMED_FRAUD", "fraud_type": "synthetic_identity", "amount_range": "5000-10000", "country": "NL"}
    },
    {
        "case_id": "CASE-018",
        "summary": "Elderly customer victim of authorised push payment fraud — telephone banking scam impersonating bank security team. EUR 22,000 transferred to fraudster. Vulnerability flag added to account. Customer fully reimbursed.",
        "metadata": {"outcome": "VULNERABLE_CUSTOMER", "fraud_type": "authorised_push_payment", "amount_range": "10000-25000", "country": "NL"}
    },
    {
        "case_id": "CASE-019",
        "summary": "Crypto exchange withdrawal to unhosted wallet — transaction review per FATF travel rule. Customer provided wallet ownership proof. Transaction allowed after 24h review. No AML concerns identified.",
        "metadata": {"outcome": "CLEARED", "fraud_type": "crypto_withdrawal", "amount_range": "5000-25000", "country": "NL"}
    },
    {
        "case_id": "CASE-020",
        "summary": "Ransomware payment attempt — customer coerced into purchasing crypto to pay ransomware attackers. Bank intervention stopped transaction. Customer referred to national cybercrime unit. Crypto purchase blocked.",
        "metadata": {"outcome": "BLOCKED", "fraud_type": "ransomware_payment", "amount_range": "5000-25000", "country": "NL"}
    },
]
