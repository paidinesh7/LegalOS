"""Prompt for Impact Assessment."""

IMPACT_PROMPT = """Based on your full analysis of this document, provide a comprehensive \
impact assessment for the founder:

1. **Impact Scores** (1-10 scale)
   - **Control Score** (1 = full founder control, 10 = investor dominance)
     Consider: board composition, veto rights breadth, reserved matters, voting rights
   - **Economics Score** (1 = founder-friendly economics, 10 = investor-heavy)
     Consider: liquidation preference type/multiple, anti-dilution, ESOP dilution, participation rights
   - **Flexibility Score** (1 = full founder flexibility, 10 = heavily restricted)
     Consider: non-compete, lock-in, transfer restrictions, operational consent requirements
   For each score, provide a clear rationale.

2. **Exit Waterfall Analysis**
   Calculate approximate founder vs investor returns at different exit multiples:
   - 2x exit (modest outcome)
   - 5x exit (good outcome)
   - 10x exit (great outcome)
   Use the actual investment amount and terms from the document. Show the exit valuation, \
   what investors get, and what founders get at each multiple. Account for liquidation \
   preferences, participation rights, and conversion mechanics.

3. **Top Negotiation Items** (ranked by priority)
   List the most important items the founder should negotiate, in order of priority. For each:
   - What the current language says
   - What the founder should push for
   - Why this matters
   - Specific alternative language to propose

Focus on items that have the highest practical impact on founder outcomes. Deprioritize \
items that are already market-standard or have minimal real-world impact."""
