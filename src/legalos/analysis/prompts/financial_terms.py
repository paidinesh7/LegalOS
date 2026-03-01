"""Prompt for Financial Terms analysis."""

FINANCIAL_TERMS_PROMPT = """Analyze the document for FINANCIAL TERMS. Extract and assess:

1. **Valuation**
   - Pre-money valuation
   - Post-money valuation
   - Fully diluted share capital used for calculation
   - Whether ESOP pool is included in pre-money (increases founder dilution)

2. **Investment Amount & Instruments**
   - Total investment amount
   - Instrument type (CCPS, CCD, equity, SAFE, convertible note)
   - Price per share (face value + premium)
   - Number of shares being issued

3. **Tranches**
   - Whether investment is in single or multiple tranches
   - Tranche amounts and timelines
   - Milestone conditions for subsequent tranches
   - What happens if milestones are not met (reduced valuation? cancellation?)
   - Whether the company operates at lower capitalization between tranches

4. **Conditions Precedent (CPs)**
   - CPs for first closing
   - CPs for subsequent tranches
   - Regulatory approvals required (RBI FC-GPR filing, FEMA compliance)
   - Legal/tax due diligence conditions
   - Timeline for satisfaction of CPs
   - Long-stop date and consequences of non-satisfaction

5. **Use of Proceeds**
   - Any restrictions on how funds can be used
   - Whether a detailed use-of-proceeds schedule is attached
   - Approval requirements for deviation from stated use

6. **Costs & Expenses**
   - Who bears transaction costs (legal, DD, stamp duty)
   - Cap on investor legal fees borne by company
   - Ongoing compliance cost obligations

Flag especially:
- Milestone-based tranches without clear definitions (subjective milestones)
- CPs that give investors an easy exit option (overly broad MAC clauses)
- Use-of-proceeds restrictions that limit operational flexibility
- Company bearing uncapped investor legal fees
- Valuation calculated on a basis unfavorable to founders"""
