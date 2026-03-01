"""Prompt for Control Provisions analysis."""

CONTROL_PROMPT = """Analyze the document for CONTROL PROVISIONS. Extract and assess every clause \
related to governance and decision-making power:

1. **Board Composition**
   - Number of board seats and allocation (founder-nominated vs investor-nominated vs independent)
   - Chairperson appointment and casting vote rights
   - Observer rights and board meeting quorum requirements
   - Board committee composition (audit, nomination, compensation)

2. **Voting Rights**
   - Differential voting rights (if any)
   - Ordinary resolution vs special resolution thresholds
   - Shareholder meeting quorum requirements
   - Voting agreements or pooling arrangements

3. **Protective Provisions / Veto Rights (Affirmative Vote / Reserved Matters)**
   - Complete list of matters requiring investor consent
   - Whether these apply at board level, shareholder level, or both
   - Sunset provisions on veto rights
   - Carve-outs and thresholds (e.g., "expenditure above ₹X requires consent")

4. **Reserved Matters**
   - Issuance of new securities
   - Changes to articles/memorandum
   - Related party transactions
   - Borrowing limits
   - Business plan/budget approval
   - Hiring/firing of key personnel
   - Amendment of ESOP plan

For each finding, assess whether the provision is founder-friendly, market-standard, or \
investor-heavy. Pay special attention to:
- Whether the list of reserved matters is unusually broad
- Whether investor veto extends to operational decisions (red flag)
- Whether there's a deadlock resolution mechanism
- Quorum requirements that give investors effective veto power"""
