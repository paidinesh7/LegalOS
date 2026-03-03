"""Quick scan prompt — consolidated single-pass analysis for founder-first red flags."""

QUICK_SCAN_BASE_PROMPT = """Perform a QUICK SCAN of this document from the founder's perspective.
Cover ALL areas (control, capital, investor rights, exit, founder obligations, financial terms).

Output:
1. overall_risk: one word (low/medium/high/critical)
2. bottom_line: 2-3 sentences — deal posture, biggest concern, recommendation
3. red_flags: 5-8 most critical findings. For each:
   - clause_reference, title, severity
   - what_it_says: 1-sentence clause summary
   - why_its_a_problem: 1-sentence founder perspective
   - pushback: specific counter-argument or negotiation language
4. investor_asks: 3-5 key things the investor is requesting
5. must_negotiate: top 3-5 imperative pushback items with rationale

{type_emphasis}

RULES:
- Max 8 red flags, prioritized by founder impact.
- Each text field max 25 words.
- pushback must be SPECIFIC (e.g., "Request weighted average instead of full ratchet")
- Flag what IS standard too — founders need to know what's normal."""

_TYPE_EMPHASIS = {
    "term_sheet": """TERM SHEET EMPHASIS:
Focus on: valuation mechanics (pre/post-money, ESOP pool placement), anti-dilution type,
liquidation preference (participating vs non-participating, multiple), board composition,
founder vesting/lock-in. These are where founders most often get burned.""",

    "sha": """SHA EMPHASIS:
Focus on: protective provisions/reserved matters breadth, drag-along mechanics,
exit timeline and put options, non-compete scope (Indian law enforceability),
indemnification caps, deadlock resolution. SHAs lock in governance for years.""",

    "ssa": """SSA EMPHASIS:
Focus on: conditions precedent (achievable? timeline?), representations & warranties scope,
MAC clause breadth, tranche conditions, use of proceeds restrictions,
closing mechanics and long-stop date. SSAs have binding financial terms.""",
}


def build_quick_scan_prompt(document_type: str = "") -> str:
    """Build the quick scan prompt with optional doc-type emphasis."""
    doc_key = document_type.lower().replace(" ", "_").replace("-", "_") if document_type else ""
    emphasis = _TYPE_EMPHASIS.get(doc_key, "")
    return QUICK_SCAN_BASE_PROMPT.format(type_emphasis=emphasis)
