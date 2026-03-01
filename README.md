# LegalOS

AI-powered legal document analyzer for Indian startup founders. Analyze term sheets, shareholder agreements, and share subscription agreements — understand every clause, assess founder impact, and generate redline comments ready for investor counsel.

## What It Does

Feed it your fundraising documents and get:

1. **Interactive HTML Report** — every clause analyzed, severity-coded (standard / aggressive / unusual / missing), explained in plain English
2. **Impact Dashboard** — control, economics, and flexibility scores (1-10) plus exit waterfall analysis at 2x/5x/10x
3. **Redlined DOCX** — margin comments with counter-proposals and alternative language, ready to send to lawyers
4. **Terminal Q&A** — ask follow-up questions about the document with full conversation context

## Quick Start

```bash
pip install -e .
export ANTHROPIC_API_KEY=sk-ant-xxxxx

# Analyze a term sheet
legalos analyze ./termsheet.pdf --model sonnet

# Generate redline comments on a SHA
legalos redline ./sha.docx --model opus --author "Founder Name"
```

## Usage

### Analyze Documents

```bash
# Single file (PDF, DOCX, or image)
legalos analyze ./termsheet.pdf

# All supported files in a directory
legalos analyze ./deal-docs/

# Use Opus for highest quality analysis
legalos analyze ./sha.pdf --model opus

# Skip Q&A, don't auto-open browser
legalos analyze ./docs/ --no-qa --no-browser

# See token usage and cost
legalos analyze ./docs/ -v
```

### Generate Redline

```bash
legalos redline ./sha.docx --author "Priya Sharma"
# Produces sha_redlined.docx with margin comments
```

### Q&A Session

After `analyze` runs, the terminal drops into an interactive Q&A:

```
You: What happens if we raise a down round?
LegalOS: Based on Clause 7.3, the anti-dilution mechanism is full ratchet...

You: What's the worst case at a 2x exit?
LegalOS: With the 1x participating liquidation preference in Clause 9.1...

You: quit
```

## Analysis Coverage

| Section | What It Extracts |
|---------|-----------------|
| Control Provisions | Board composition, voting rights, protective provisions, veto rights, reserved matters |
| Capital Structure | Authorized capital, ESOP pool, conversion ratios, anti-dilution mechanisms |
| Investor Rights | Pre-emptive, tag-along, drag-along, ROFR/ROFO, information rights |
| Key Events & Exit | Liquidation preferences, exit provisions, IPO conditions, put/call options |
| Founder Obligations | Non-compete, lock-in, reps & warranties, indemnification |
| Financial Terms | Valuation, investment amount, tranches, milestones, conditions precedent |
| Plain English Guide | Every complex term explained with real-world Indian startup examples |
| Impact Assessment | Control/economics/flexibility scores, exit waterfall, top negotiation items |

Every finding includes: clause reference, exact quoted text, severity rating, plain English explanation, founder impact, and actionable recommendation.

## Models

| Flag | Model | Best For |
|------|-------|----------|
| `--model haiku` | Claude Haiku 4.5 | Quick first-pass reads, cheapest |
| `--model sonnet` | Claude Sonnet 4 | Default — good balance of quality and cost |
| `--model opus` | Claude Opus 4 | Final analysis before signing, catches subtle issues |

## Supported File Types

- **PDF** — text-based and scanned (OCR fallback via pymupdf)
- **DOCX** — preserves heading structure and tables
- **Images** — PNG, JPG, TIFF, BMP, WebP (requires `pip install legalos[ocr]`)

## How Founders Should Use This

1. **Receive documents** from investor counsel
2. **Run `legalos analyze`** — read the HTML report, note the red/orange flags
3. **Check impact scores** — control score 7+ means you're giving up too much governance
4. **Use Q&A** to ask about exit scenarios, dilution, specific clauses
5. **Run `legalos redline`** on the DOCX — get a marked-up version with counter-proposals
6. **Send the redline** to your lawyer for review, then to investor counsel
7. **Re-analyze** the revised draft to confirm changes landed

## Project Structure

```
src/legalos/
├── cli.py                  # Click CLI (analyze, redline commands)
├── config.py               # Model mapping, pricing, API key config
├── parsing/                # PDF, DOCX, image parsers + chunker
├── analysis/
│   ├── client.py           # Anthropic SDK with prompt caching
│   ├── engine.py           # 8-pass analysis orchestrator
│   ├── schemas.py          # Pydantic models for structured output
│   └── prompts/            # Specialized prompts per section
├── report/                 # Jinja2 HTML report generator
├── redline/                # DOCX comment annotation
├── qa/                     # Interactive terminal Q&A
└── utils/                  # Errors, progress bars
```

## Cost Efficiency

Uses Anthropic's prompt caching — the document text is cached across all 8 analysis passes. For a typical run on Sonnet, the document is billed once at cache-write rate and 7 times at cache-read rate (~70% input cost savings). Use `-v` to see exact costs.

## Disclaimer

This tool provides AI-generated analysis and should not be treated as legal advice. Always have a qualified lawyer review documents before signing.
