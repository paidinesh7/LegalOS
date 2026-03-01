"""Prompt for Redline comment generation."""

REDLINE_PROMPT = """Analyze this document and generate redline comments for every clause that \
a founder should negotiate, push back on, or seek clarification about.

For each comment, provide:
1. **target_text**: The EXACT text from the document that the comment should be anchored to. \
   Copy it character-for-character. This will be used to find and highlight the text in the document.
2. **severity**: "standard" (informational), "aggressive" (investor-heavy but negotiable), \
   "unusual" (non-market, flag strongly), or "missing" (important clause not present)
3. **issue**: What the problem or concern is
4. **suggestion**: What the founder should ask for
5. **alternative_language**: Specific redrafted language to propose (if applicable)
6. **reasoning**: Why this change matters, with market context

Guidelines:
- Be precise with target_text — it must be findable in the original document
- For "missing" severity items, use the most relevant nearby text as the anchor
- Focus on substantive issues, not formatting or minor drafting style
- Prioritize comments that have real economic or control impact
- Include positive comments too ("This is a market-standard provision — no change needed") \
  for key clauses, but mark them as "standard" severity
- Suggest specific alternative language that a founder could send to investor counsel
- Each comment should be self-contained and actionable"""
