"""Prompt for Investor Rights analysis."""

INVESTOR_RIGHTS_PROMPT = """Analyze the document for INVESTOR RIGHTS. Extract and assess:

1. **Pre-emptive Rights / Right of First Offer**
   - Scope: applies to all future issuances or only specific types
   - Exercise period and notice requirements
   - Consequences of non-exercise
   - Whether founders have matching pre-emptive rights

2. **Tag-Along Rights (Co-Sale)**
   - Trigger: any founder share transfer or only above a threshold
   - Pro-rata or full tag-along
   - Exceptions (inter-se transfers, ESOP-related transfers)
   - Notice and exercise mechanics

3. **Drag-Along Rights**
   - Who can trigger drag-along (investor majority? specific investor?)
   - Minimum valuation or return thresholds for triggering
   - Floor price protections for founders
   - Timeline for completing the drag-along transaction
   - Whether drag can be triggered by a single investor (red flag)

4. **Right of First Refusal (ROFR) / Right of First Offer (ROFO)**
   - Who holds ROFR/ROFO
   - Exercise period
   - Whether it applies to ALL transfers or only above a threshold
   - Interaction with tag-along and drag-along

5. **Information Rights**
   - Financial reporting obligations (monthly/quarterly/annual)
   - Board meeting frequency and notice period
   - Inspection rights
   - Whether information rights are proportionate or all-or-nothing

6. **Other Investor Protections**
   - Most Favored Nation (MFN) clauses
   - Anti-embarrassment provisions
   - Key person insurance requirements
   - D&O insurance

Flag especially:
- Drag-along without minimum return thresholds (forces founders to sell at any price)
- ROFR on ALL transfers including small amounts (restricts founder liquidity)
- Overly broad information rights that create operational burden
- Tag-along that triggers on inter-se founder transfers"""
