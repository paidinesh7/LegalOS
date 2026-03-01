"""Prompt for Capital Structure analysis."""

CAPITAL_PROMPT = """Analyze the document for CAPITAL STRUCTURE provisions. Extract and assess:

1. **Authorized & Paid-up Capital**
   - Current authorized share capital and proposed increases
   - Break-up between equity and preference shares
   - Face value and premium per share

2. **ESOP Pool**
   - Size of the ESOP pool (% of fully diluted capital)
   - Whether the pool is pre-money or post-money (critical for founder dilution)
   - Vesting schedule terms
   - Who bears the dilution from the ESOP pool
   - Whether future ESOP expansion requires investor consent

3. **Conversion Rights**
   - Preference share to equity conversion ratio
   - Conversion triggers (automatic vs optional)
   - Conversion at IPO — mandatory or optional for investors
   - Adjustments to conversion ratio

4. **Anti-Dilution Protection**
   - Type: Full ratchet vs weighted average (broad-based vs narrow-based)
   - Trigger events (down rounds, specific issuances)
   - Carve-outs (ESOPs, strategic issuances)
   - Pay-to-play provisions

5. **Pre-emptive / Pro-rata Rights on Future Rounds**
   - Who has pro-rata participation rights
   - Super pro-rata rights (flag if present)
   - Major investor thresholds

For each finding, flag:
- Full ratchet anti-dilution (aggressive — weighted average is market standard)
- Pre-money ESOP pools (founder bears full dilution)
- Broad anti-dilution without standard carve-outs
- Unusual conversion mechanics that benefit investors in exit scenarios"""
