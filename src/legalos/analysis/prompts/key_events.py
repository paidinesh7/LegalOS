"""Prompt for Key Events & Exit analysis."""

KEY_EVENTS_PROMPT = """Analyze the document for KEY EVENTS & EXIT provisions. Extract and assess:

1. **Liquidation Preference**
   - Type: participating vs non-participating
   - Multiple: 1x, 2x, or higher
   - Participation cap (if participating)
   - Seniority/priority among investor classes (pari passu vs waterfall)
   - Definition of "liquidation event" (does it include deemed liquidation?)

2. **Exit Provisions**
   - Investor put options (forced buyback) — trigger events and timeline
   - Call options
   - Exit timeline / sunset clauses
   - Forced exit mechanisms after a specified period
   - Whether founders can be forced to find a buyer

3. **IPO Provisions**
   - Qualified IPO definition (minimum valuation, exchange requirements)
   - Lock-up period post-IPO for founders vs investors
   - Automatic conversion of preference shares at IPO
   - IPO ratchet (price protection for investors at IPO)
   - Who controls IPO timing

4. **Deemed Liquidation Events**
   - What triggers deemed liquidation (merger, acquisition, asset sale)
   - Whether change of control triggers deemed liquidation
   - Thresholds for triggering

5. **Put/Call Options**
   - Investor put option terms and pricing formula
   - Call option in favor of founders or company
   - Pricing mechanism (fair market value, formula-based, floor price)
   - Exercise windows and notice periods

Flag especially:
- Participating liquidation preference above 1x (very aggressive)
- Put options that force founders to buy back at a premium
- Deemed liquidation including ordinary business changes
- IPO ratchet mechanisms (investors get extra shares if IPO price is low)
- No sunset on exit rights (investors can force exit indefinitely)"""
