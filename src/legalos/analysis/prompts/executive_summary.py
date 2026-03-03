"""Prompt for the executive summary pass."""

EXECUTIVE_SUMMARY_PROMPT = """Generate an executive summary for the founder.

1. overall_risk: single word (low/medium/high/critical) based on the aggregate risk across all sections.
2. bottom_line: 2-3 sentences — deal posture (investor-friendly, balanced, founder-friendly), the single biggest concern, and a clear recommendation.
3. must_negotiate: exactly 3 imperative action items, each like "Push back on X — request Y".

Keep total output under 200 tokens."""
