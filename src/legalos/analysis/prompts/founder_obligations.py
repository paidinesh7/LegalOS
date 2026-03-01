"""Prompt for Founder Obligations analysis."""

FOUNDER_OBLIGATIONS_PROMPT = """Analyze the document for FOUNDER OBLIGATIONS. Extract and assess:

1. **Non-Compete & Non-Solicitation**
   - Duration (during employment and post-departure)
   - Geographic scope
   - Scope of restricted activities
   - Whether it's enforceable under Indian law (Section 27, Indian Contract Act)
   - Non-solicitation of employees and customers

2. **Full-Time Commitment / Exclusivity**
   - Whether founders must devote 100% time
   - Restrictions on other business activities, advisory roles, angel investing
   - Approval requirements for outside activities
   - What happens if a founder wants to pursue other interests

3. **Lock-In Period**
   - Duration of founder lock-in (typically 3-5 years)
   - Vesting of founder shares
   - Accelerated vesting triggers (termination without cause, change of control)
   - Consequences of early departure (share forfeiture, buyback at par)

4. **Representations & Warranties**
   - Scope of founder reps (personal vs company)
   - Survival period for reps & warranties
   - Whether reps are qualified by knowledge/materiality
   - Cap on liability for breach of reps

5. **Indemnification**
   - Scope of founder indemnification obligations
   - Cap on indemnification (should be capped at investment amount, not unlimited)
   - Basket/threshold before indemnification kicks in
   - Time limit for claims
   - Whether indemnification is joint & several among founders

6. **Other Obligations**
   - Key man provisions (what happens if founder leaves/is incapacitated)
   - IP assignment obligations
   - Confidentiality obligations post-exit

Flag especially:
- Non-compete extending beyond employment period (may be unenforceable in India but still creates risk)
- Unlimited indemnification or indemnification exceeding investment amount
- Share forfeiture at par value for early departure (punitive)
- Joint and several indemnification (one founder bears liability for another's breach)
- Lock-in without accelerated vesting on termination without cause"""
