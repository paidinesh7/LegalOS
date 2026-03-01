"""Prompt for Plain English term explanations."""

EXPLAINER_PROMPT = """Based on your analysis of this document, identify every complex legal or \
financial term that a non-lawyer startup founder might not understand. For each term:

1. Provide a clear, plain English definition (no legal jargon)
2. Give a concrete real-world example relevant to an Indian startup context
3. Explain why this term matters for the founder specifically

Cover terms including but not limited to:
- Liquidation preference (participating vs non-participating)
- Anti-dilution (full ratchet vs weighted average)
- Protective provisions / affirmative vote matters
- Tag-along and drag-along rights
- Right of First Refusal (ROFR) and Right of First Offer (ROFO)
- Pre-emptive rights / pro-rata rights
- Conversion ratio and automatic conversion
- Deemed liquidation event
- Representations and warranties
- Indemnification
- Conditions precedent
- CCPS (Compulsory Convertible Preference Shares)
- ESOP pool (pre-money vs post-money)
- Vesting and cliff period
- Lock-in period
- Non-compete and non-solicitation
- Material adverse change (MAC)
- Reserved matters / affirmative vote items

Only include terms that actually appear in or are relevant to this specific document. \
Do not include generic terms not referenced in the document."""
