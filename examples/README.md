# Examples

Sample files so you can see what LegalOS produces before running your own analysis.

## What's Here

| File | What It Is |
|------|-----------|
| `NexaFlow_Series_A_TermSheet.docx` | A sample Series A term sheet for a fictional startup (NexaFlow). Use this as input to LegalOS. |
| `sample_report.html` | The HTML report LegalOS generated from that term sheet. Open it in your browser to see what you'll get. |

## Founder Guides

Plain-English explainers for Indian startup founders — no API key needed, just open in your browser.

| Guide | What It Covers |
|-------|---------------|
| [`guide_term_sheet.html`](guide_term_sheet.html) | Valuation, liquidation preference, anti-dilution, board composition, ESOP, founder vesting, non-compete, conditions precedent, exclusivity — with green/orange/red severity examples and a pre-signing checklist. |
| [`guide_sha.html`](guide_sha.html) | Board rights, reserved matters, transfer restrictions (ROFR/tag/drag), information rights, founder obligations, exit provisions, indemnification, dispute resolution — with an SHA review checklist. |
| [`guide_ssa.html`](guide_ssa.html) | CCPS mechanics, conditions precedent, representations & warranties, covenants, closing mechanics — with an SSA review checklist. |

Each guide uses the same severity color scheme as LegalOS reports: **green** (standard/founder-friendly), **orange** (aggressive/negotiate), **red** (unusual/walk away). All examples use concrete INR figures from typical Indian startup fundraises.

## Try It Yourself

**Just want to see the report?** Open `sample_report.html` in your browser — no API key needed.

**Want to run the analysis yourself?**

```
legalos analyze examples/
```

This will parse the sample term sheet and generate a fresh report. You'll need your API key set up first (see the main [README](../README.md#setup-one-time)).

## What to Look For in the Report

- **Severity colors** — green (standard), orange (aggressive), red (unusual). Scroll through the findings to see how each clause is rated.
- **Impact scores** — the Control, Economics, and Flexibility gauges at the top show how much you're giving up, rated 1-10.
- **Negotiation priorities** — a ranked list of what to push back on, with suggested alternative language.
- **Thumbs up/down buttons** — click these on individual findings to rate them. The report will generate a CLI command you can paste to save your feedback.
