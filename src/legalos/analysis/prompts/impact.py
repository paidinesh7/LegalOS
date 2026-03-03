"""Prompt for Impact Assessment."""

IMPACT_PROMPT = """Provide a founder impact assessment. Keep ALL text fields under 15 words each.

1. **Impact Scores** (1-10 scale, each rationale under 15 words):
   - control_score: 1=founder control, 10=investor dominance
   - economics_score: 1=founder-friendly, 10=investor-heavy
   - flexibility_score: 1=full flexibility, 10=heavily restricted

2. **Exit Waterfall** — 3 rows (2x, 5x, 10x exit). Use actual investment amounts. \
Each field under 15 words.

3. **Top 3 Negotiation Items** — ranked by priority. For each:
   - current_language: what the doc says (under 15 words)
   - suggested_change: what to push for (under 15 words)
   - reasoning: why it matters (under 15 words)

Keep total output under 600 tokens. Be extremely concise."""
