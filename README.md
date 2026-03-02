# LegalOS

AI-powered legal document analyzer for Indian startup founders. Analyze term sheets, shareholder agreements, and other fundraising documents — understand every clause, assess founder impact, get negotiation guidance, and generate redline comments ready for investor counsel.

Built on Claude with prompt caching, structured output, and a multi-pass analysis pipeline that acts like a senior Indian startup lawyer reviewing your documents.

---

## Table of Contents

- [What It Does](#what-it-does)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Core Commands](#core-commands)
  - [Analyze Documents](#analyze-documents)
  - [Generate Redline](#generate-redline)
  - [Interactive Q&A](#interactive-qa)
- [Founder Profile](#founder-profile)
  - [Setup](#profile-setup)
  - [Managing Your Profile](#managing-your-profile)
  - [Deal Contexts](#deal-contexts)
- [Knowledge Base](#knowledge-base)
  - [How It Works](#how-it-works)
  - [CLI Commands](#kb-commands)
  - [Export & Share](#export--share)
- [Feedback Loop](#feedback-loop)
  - [Post-Analysis Feedback](#post-analysis-feedback)
  - [Per-Finding Votes](#per-finding-votes)
- [Analysis Coverage](#analysis-coverage)
- [How the Analysis Pipeline Works](#how-the-analysis-pipeline-works)
- [Supported File Types](#supported-file-types)
- [Models & Cost](#models--cost)
- [Project Structure](#project-structure)
- [Workflow Guide](#workflow-guide)
- [Configuration](#configuration)
- [Disclaimer](#disclaimer)

---

## What It Does

Feed it your fundraising documents and get:

1. **Interactive HTML Report** — every clause analyzed, severity-coded (standard / aggressive / unusual / missing), explained in plain English with founder-specific impact and negotiation recommendations
2. **Impact Dashboard** — control, economics, and flexibility scores (1-10) with rationale, plus exit waterfall analysis at 2x/5x/10x multiples
3. **Top Negotiation Priorities** — ranked list of what to push back on, with current language, suggested changes, and reasoning
4. **Plain English Guide** — every complex legal term explained with real-world Indian startup examples
5. **Redlined DOCX** — margin comments with counter-proposals and alternative language, ready to send to lawyers
6. **Terminal Q&A** — ask follow-up questions about the document with full conversation context
7. **Legal Team Brief** — paste or load your lawyer's guidance (free text, .txt, .md, .pdf, .docx) and it's injected into every analysis prompt
8. **Knowledge Base** — accumulated legal insights from every analysis, injected into future reviews so the AI learns from your experience
9. **Feedback Loop** — tell LegalOS what it missed or over-flagged and it adjusts in future sessions

---

## Quick Start

```bash
pip install -e .
export ANTHROPIC_API_KEY=sk-ant-xxxxx

# Set up your founder profile (optional but recommended)
legalos init

# Or pre-load your lawyer's notes during setup
legalos init --legal-brief ./lawyer-notes.txt

# Analyze a term sheet
legalos analyze ./termsheet.pdf

# Analyze with a per-session legal brief override
legalos analyze ./termsheet.pdf --legal-brief ./lawyer-notes.txt

# Generate redline comments on a SHA
legalos redline ./sha.docx --author "Founder Name"
```

---

## Installation

### Requirements

- Python 3.10+
- An [Anthropic API key](https://console.anthropic.com/)

### Install

```bash
# Clone and install in development mode
git clone <repo-url> && cd LegalOS
pip install -e .

# For scanned document / image OCR support
pip install -e ".[ocr]"
```

### Environment

```bash
# Required
export ANTHROPIC_API_KEY=sk-ant-xxxxx

# Or create a .env file
cp .env.example .env
# Edit .env with your API key
```

---

## Core Commands

### Analyze Documents

```bash
# Single file (PDF, DOCX, or image)
legalos analyze ./termsheet.pdf

# All supported files in a directory
legalos analyze ./deal-docs/

# Use Opus for highest quality analysis
legalos analyze ./sha.pdf --model opus

# Specify document type (auto-detected if omitted)
legalos analyze ./doc.pdf --type sha

# Apply a deal context for tailored analysis
legalos analyze ./termsheet.pdf --deal "Series A"

# Skip Q&A session and feedback prompts
legalos analyze ./doc.pdf --no-qa --no-feedback

# Don't auto-open the report in browser
legalos analyze ./doc.pdf --no-browser

# Override legal team brief for this session (doesn't modify saved profile)
legalos analyze ./doc.pdf --legal-brief ./lawyer-notes.txt

# See token usage, costs, and prompt details
legalos analyze ./doc.pdf -v

# Custom output path
legalos analyze ./doc.pdf -o ./reports/analysis.html
```

**What happens during `analyze`:**

1. Parses the document (PDF text extraction, DOCX structure preservation, or OCR for images)
2. Loads your founder profile, feedback history, and knowledge base
3. Runs 8 analysis passes through Claude (6 sections + explainer + impact assessment)
4. Generates an interactive HTML report and opens it in your browser
5. Drops into an interactive Q&A session (unless `--no-qa`)
6. Collects feedback on the analysis quality (unless `--no-feedback`)
7. Auto-captures learnings from aggressive findings and negotiation items
8. Offers you a chance to record a manual insight

### Generate Redline

```bash
# Basic redline — produces sha_redlined.docx
legalos redline ./sha.docx

# Custom author name for comments
legalos redline ./sha.docx --author "Priya Sharma"

# Use Opus for maximum quality, apply deal context
legalos redline ./sha.docx --model opus --deal "Series A"

# Custom output path
legalos redline ./sha.docx -o ./marked-up-sha.docx
```

The redline command generates a copy of your DOCX with inline comments containing:
- Severity level (CRITICAL / HIGH / MEDIUM / LOW)
- The issue identified
- Suggested alternative language
- Reasoning for the change

Comments are matched to exact text locations in the document using fuzzy matching (0.85 similarity threshold) so minor formatting differences don't cause misses. Any unmatched comments are collected at the start of the document.

### Interactive Q&A

After `analyze` completes, the terminal drops into a multi-turn Q&A session:

```
You: What happens if we raise a down round?
LegalOS: Based on Clause 7.3, the anti-dilution mechanism is full ratchet,
         which means existing investors' conversion price adjusts to the
         new lower price. This could dilute founders by up to...

You: What's the worst case at a 2x exit?
LegalOS: With the 1x participating liquidation preference in Clause 9.1,
         investors first recover their investment, then participate pro-rata
         in remaining proceeds. At a 2x exit valuation...

You: feedback
[Opens feedback dialog mid-session]

You: quit
```

The Q&A maintains full conversation history and has access to the complete document text via prompt caching. You can ask about specific clauses, exit scenarios, dilution math, comparisons to market standards, or anything else about the document.

**Commands during Q&A:**
- Type any question to get an answer
- `feedback` — open the feedback dialog without leaving Q&A
- `quit` / `exit` / `q` — end the session

---

## Founder Profile

The profile personalizes every analysis to your company's situation. Without a profile, LegalOS still works — but with one, it gives extra scrutiny to your priority areas, adjusts flagging sensitivity to your risk tolerance, and uses your deal parameters for waterfall calculations.

### Profile Setup

```bash
legalos init
```

The interactive wizard walks you through five steps:

**Step 1 — Company Context**
- Company name, sector, funding stage (Pre-Seed through Series D+)
- Current and previous round names

**Step 2 — Legal Priorities**
- High-priority areas (board control, liquidation preference, anti-dilution, etc.)
- Custom watchlist — terms to ALWAYS flag regardless of severity
- Document-type overrides — extra priorities for specific document types (e.g., extra scrutiny on conversion ratios for term sheets)

**Step 3 — Risk Tolerance**
- **Conservative** — Flag everything that deviates even slightly from market-standard terms
- **Balanced** (default) — Flag aggressive and unusual terms; note standard terms briefly
- **Aggressive** — Only flag truly unusual or materially disadvantageous terms

**Step 4 — Deal Context**
- Investor names, lead investor, deal size, pre-money valuation
- Used for exit waterfall calculations and negotiation weighting

**Step 5 — Legal Team Brief**
- Free-text guidance from your lawyer or legal team
- Three input modes: **type** (paste text directly), **file** (load from .txt/.md/.pdf/.docx), or **skip**
- Can also be pre-loaded via `legalos init --legal-brief ./notes.txt`
- Injected as `<legal_team_guidance>` into every analysis prompt so the AI follows your lawyer's specific instructions

All fields are optional — press Enter to skip anything.

### Managing Your Profile

```bash
# View current profile
legalos profile

# Update specific fields
legalos profile set risk_tolerance conservative
legalos profile set company.name "Acme Corp"
legalos profile set company.stage series_a
legalos profile set priorities.high_priority_areas "Board control, Anti-dilution, Liquidation preference"
legalos profile set priorities.custom_watchlist "Full ratchet, Drag-along below 75%"
legalos profile set deal.deal_size "INR 15Cr"
legalos profile set deal.investor_names "Sequoia, Accel"

# Set legal team brief
legalos profile set legal_team_brief "Watch for full ratchet, non-compete beyond 1yr, any put options before 5yr"

# Delete profile
legalos profile clear

# Share with co-founders or advisors
legalos profile export ./my-profile.json
legalos profile import ./teammate-profile.json
```

### Deal Contexts

Deal contexts are reusable overlays that add deal-specific parameters on top of your base profile. Useful when evaluating multiple term sheets simultaneously.

```bash
# Create a deal context
legalos deal add "Series A"
# Interactive prompts for: investors, lead investor, deal size, valuation, extra watchlist

# List all deals
legalos deal

# View deal details
legalos deal show "Series A"

# Use during analysis
legalos analyze ./termsheet.pdf --deal "Series A"

# Remove a deal
legalos deal remove "Series A"
```

When you use `--deal`, the deal's investor names, deal size, valuation, and extra watchlist items are merged into your profile for that analysis run.

---

## Knowledge Base

Founders accumulate legal insights across multiple document reviews — which clauses to push back on, what negotiation tactics worked, which red flags are deal-breakers. The knowledge base captures and reuses these learnings.

### How It Works

**Auto-capture:** After every analysis, LegalOS automatically extracts learnings from:
- High-severity findings in high/critical risk sections (e.g., "Found full-ratchet anti-dilution in SHA")
- Top negotiation priorities from the impact assessment (e.g., "Negotiation priority: Remove drag-along threshold below 75%")
- Previously-missed items now being caught (from the feedback effectiveness loop)

**Prompt injection:** When you run future analyses, relevant learnings are injected into the AI's prompts:
- System-level: Top 10 most-referenced learnings across all categories
- Section-level: Up to 5 learnings relevant to each specific analysis section (matched by section keywords and tags)

This means the AI gets better at analyzing your documents over time — it knows what you've seen before, what you care about, and what negotiation outcomes you've achieved.

**Manual notes:** After auto-capture, you're offered a chance to record your own insight. You can also add learnings anytime via `legalos kb add`.

### KB Commands

```bash
# View summary (count by category, top tags, most referenced)
legalos kb

# List all entries with IDs, categories, dates
legalos kb show

# Add a learning interactively
legalos kb add
# Prompts: insight text, title, category, tags

# Search by keyword (also supports --category and --section filters)
legalos kb search "anti-dilution"
legalos kb search "board" --category clause_pattern
legalos kb search "veto" --section control_provisions

# Edit an existing entry
legalos kb update <id>

# Delete an entry
legalos kb remove <id>

# Export as Markdown (to stdout or file)
legalos kb export
legalos kb export -o learnings.md

# Import from another founder's JSON export
legalos kb import ./teammate-learnings.json

# Clear all learnings (with confirmation)
legalos kb clear
```

### Learning Categories

| Category | What Goes Here | Example |
|----------|---------------|---------|
| `clause_pattern` | Patterns observed in legal clauses | "Weighted anti-dilution is standard at Series A — full ratchet is aggressive" |
| `negotiation` | Negotiation outcomes and tactics | "Pushed back on full-ratchet, got weighted-average" |
| `red_flag` | Deal-breaker patterns | "Deemed liquidation without consent = deal-breaker" |
| `decision` | Decisions made and rationale | "Accepted 1x non-participating liquidation pref" |
| `market_insight` | Industry benchmarks and norms | "Most Series A leads want 1 board seat" |
| `general` | Free-form notes | Anything that doesn't fit above |

### Export & Share

The Markdown export groups learnings by category in a shareable format:

```markdown
# Legal Knowledge Base

## Clause Patterns
| Insight | Tags | Source |
|---------|------|--------|
| Weighted anti-dilution is standard at Series A | anti-dilution, series-a | Auto Analysis (SHA review) |

## Negotiation Outcomes
| What We Pushed Back On | Result | Document |
|------------------------|--------|----------|
| Full-ratchet anti-dilution | Got weighted-average | Series A SHA |

## Red Flags
- Deemed liquidation without consent (seen 2x)

## Decisions Made
- Accepted 1x non-participating liquidation preference

---
*Exported from LegalOS. 12 entries across 4 categories.*
```

JSON import/export is also available for machine-readable transfers between founders. Importing automatically deduplicates by title.

---

## Feedback Loop

LegalOS learns from your corrections. Tell it what it missed or over-flagged, and it adjusts in future sessions.

### Post-Analysis Feedback

After each analysis (and optionally during Q&A), you're prompted for:

1. **Missed items** — anything LegalOS didn't catch that it should have
2. **False positives** — findings that weren't actually relevant
3. **Additional concerns** — free-form commentary
4. **Rating** — 1-5 stars (optional)

This feedback is aggregated across sessions. In future analyses:
- Frequently missed items get `EXTRA attention` in the AI prompt
- Frequently over-flagged items get `reduced flagging` unless truly unusual
- The effectiveness loop tracks which previously-missed items are now being caught

### Per-Finding Votes

The HTML report includes thumbs-up/thumbs-down buttons on every finding. Click to rate individual findings, then export the votes as a JSON file. Import it back:

```bash
legalos feedback import ./legalos_feedback_termsheet.json
```

Downvoted findings become "false positives" in the feedback store, reducing over-flagging of similar items in future analyses.

### Managing Feedback

```bash
# View aggregated feedback summary
legalos feedback

# Import per-finding votes from HTML report
legalos feedback import ./feedback.json

# Clear all feedback history
legalos feedback clear
```

---

## Analysis Coverage

| Section | What It Extracts |
|---------|-----------------|
| **Control Provisions** | Board composition, voting rights, protective provisions, veto rights, reserved matters, quorum, deadlock |
| **Capital Structure** | Authorized capital, ESOP pool, conversion ratios, anti-dilution mechanisms, preference shares, pro-rata rights |
| **Investor Rights** | Pre-emptive rights, tag-along, drag-along, ROFR/ROFO, information rights, MFN, transfer restrictions |
| **Key Events & Exit** | Liquidation preferences, exit provisions, IPO conditions, put/call options, deemed liquidation, waterfall |
| **Founder Obligations** | Non-compete, lock-in, vesting, reps & warranties, indemnification, exclusivity, non-solicitation |
| **Financial Terms** | Valuation, investment amount, tranches, milestones, conditions precedent, use of proceeds, closing |
| **Plain English Guide** | Every complex term explained with real-world Indian startup examples |
| **Impact Assessment** | Control/economics/flexibility scores (1-10), exit waterfall at multiple scenarios, ranked negotiation items |

Every finding includes:
- **Clause reference** — exact clause number or section
- **Quoted text** — verbatim language from the document
- **Severity** — standard / aggressive / unusual / missing
- **Explanation** — what this means in plain English
- **Founder impact** — how this specifically affects you
- **Recommendation** — what to negotiate or watch for

---

## How the Analysis Pipeline Works

```
Document Input (PDF / DOCX / Image)
        |
        v
    Parse & Extract Text
    (OCR fallback for scanned docs)
        |
        v
    Chunk if needed (>150K tokens)
    (splits at clause boundaries with overlap)
        |
        v
    Build Augmented System Prompt
    +-- Base: Senior Indian startup lawyer persona
    +-- <founder_context>: company, risk tolerance, priorities, watchlist, deal params
    |   +-- <legal_team_guidance>: lawyer's brief (if provided)
    +-- <past_feedback>: aggregated missed/over-flagged patterns
    +-- <founder_learnings>: top knowledge base entries + focus areas
        |
        v
    6 Sectoral Passes (each augmented with section-specific priorities + learnings)
    |-- Control Provisions
    |-- Capital Structure
    |-- Investor Rights
    |-- Key Events & Exit
    |-- Founder Obligations
    |-- Financial Terms
        |
        v
    Explainer Pass (plain English term definitions)
        |
        v
    Impact Assessment Pass (scores + waterfall + negotiation items)
        |
        v
    Deduplicate & Merge Findings
        |
        v
    Generate HTML Report (with knowledge applied section)
        |
        v
    Interactive Q&A Session
        |
        v
    Feedback Collection + Auto-capture Learnings
```

The system prompt and document text are **cached across all 8 passes** using Anthropic's prompt caching. This means the document is billed at cache-write rate once and cache-read rate 7 times, cutting input costs by ~70%.

For large documents (>150K tokens), the text is automatically split at clause boundaries (numbered sections, article markers, headings) with a 2K-token overlap to maintain context continuity. Maximum supported document size is 500K tokens.

---

## Supported File Types

| Format | How It's Parsed | Notes |
|--------|----------------|-------|
| **PDF** | `pymupdf4llm` for markdown-formatted text | Falls back to basic `pymupdf` extraction, then OCR for scanned pages |
| **DOCX** | `python-docx` with heading structure preservation | Tables extracted as pipe-delimited rows; headings converted to markdown |
| **Images** | EasyOCR with English language support | PNG, JPG, TIFF, BMP, WebP. Requires `pip install legalos[ocr]` |

You can pass a single file or an entire directory. When given a directory, LegalOS parses all supported files (sorted by name) and analyzes them as a single combined document.

---

## Models & Cost

| Flag | Model | Best For | Input (per 1M tokens) | Output (per 1M tokens) |
|------|-------|----------|----------------------|------------------------|
| `--model haiku` | Claude Haiku 4.5 | Quick first-pass reads, cheapest | $0.80 | $4.00 |
| `--model sonnet` | Claude Sonnet 4 (default) | Good balance of quality and cost | $3.00 | $15.00 |
| `--model opus` | Claude Opus 4 | Final analysis before signing | $15.00 | $75.00 |

**Cost optimization:** Prompt caching reduces input costs significantly. For a typical Sonnet run on a 30-page document:
- Cache write: billed once at 1.25x input rate
- Cache read: billed 7 times at 0.1x input rate
- Net savings: ~70% on input costs vs. uncached

Use `-v` flag to see exact token counts and USD costs after each run.

---

## Project Structure

```
src/legalos/
├── cli.py                    # Click CLI — analyze, redline, init, profile, deal, feedback, kb
├── config.py                 # Model mapping, pricing, token limits, API key
│
├── analysis/
│   ├── client.py             # Anthropic SDK wrapper with prompt caching + retry
│   ├── engine.py             # 8-pass analysis orchestrator
│   ├── schemas.py            # Pydantic models for findings, sections, impact, redline
│   └── prompts/              # Specialized prompts per section
│       ├── system.py         # Base system prompt (senior Indian startup lawyer)
│       ├── control.py        # Control provisions section prompt
│       ├── capital.py        # Capital structure section prompt
│       ├── investor_rights.py
│       ├── key_events.py     # Key events & exit section prompt
│       ├── founder_obligations.py
│       ├── financial_terms.py
│       ├── explainer.py      # Plain English guide prompt
│       ├── impact.py         # Impact assessment prompt
│       └── redline.py        # Redline comment generation prompt
│
├── profile/
│   ├── schemas.py            # Pydantic models — profile, feedback, deals, learnings
│   ├── store.py              # JSON persistence — CRUD for all data types
│   ├── prompt_injection.py   # Dynamic prompt augmentation with context + feedback + learnings
│   ├── init_flow.py          # Interactive profile setup wizard
│   ├── auto_populate.py      # Extract profile data from analysis results
│   ├── feedback_flow.py      # Post-analysis feedback collection
│   └── learning_capture.py   # Auto-capture learnings + manual note prompt
│
├── parsing/
│   ├── base.py               # PageContent, ParsedDocument, BaseParser
│   ├── router.py             # File type detection and parser dispatch
│   ├── pdf_parser.py         # PDF text extraction with OCR fallback
│   ├── docx_parser.py        # DOCX parsing with heading structure
│   ├── image_parser.py       # EasyOCR for scanned documents
│   └── chunker.py            # Clause-boundary-aware document splitting
│
├── report/
│   ├── generator.py          # Jinja2 HTML report rendering
│   └── templates/
│       ├── report.html       # Interactive report template with per-finding feedback
│       └── styles.css        # Embedded stylesheet
│
├── redline/
│   └── generator.py          # DOCX comment annotation with fuzzy text matching
│
├── qa/
│   └── session.py            # Multi-turn Q&A with conversation memory
│
└── utils/
    ├── errors.py             # Custom exception hierarchy
    └── progress.py           # Rich console helpers — progress bars, styled output
```

### Data Storage

All user data is stored locally in `.legalos/` (project-local if it exists, otherwise `~/.legalos/`):

```
.legalos/
├── profile.json              # Founder profile
├── feedback.json             # Aggregated feedback history
├── learnings.json            # Knowledge base entries
└── deals/
    ├── series_a.json         # Deal-specific contexts
    └── bridge_round.json
```

---

## Workflow Guide

### For a new fundraising round

```bash
# 1. Set up your profile (one-time)
legalos init

# 2. Create a deal context
legalos deal add "Series A"

# 3. Analyze the first draft
legalos analyze ./termsheet.pdf --deal "Series A"

# 4. Read the report, note red/orange flags
#    Check impact scores — control score 7+ means you're giving up too much governance
#    Review the top negotiation priorities

# 5. Use Q&A to dig into specific concerns
#    "What happens if we raise a down round?"
#    "Can they block us from issuing ESOP?"

# 6. Generate a redline for your SHA
legalos redline ./sha.docx --deal "Series A" --author "Your Name"

# 7. Send the redline to your lawyer, then to investor counsel

# 8. Re-analyze the revised draft to confirm changes landed
legalos analyze ./sha_v2.pdf --deal "Series A"

# 9. Check your knowledge base — insights accumulate automatically
legalos kb
```

### Sharing learnings with your co-founder

```bash
# Founder A: export learnings
legalos kb export -o my-learnings.md        # Human-readable Markdown
legalos profile export ./profile.json       # Profile for consistent analysis

# Founder B: import
legalos profile import ./profile.json
legalos kb import ./teammate-learnings.json  # JSON format for import
```

### Reviewing multiple term sheets

```bash
# Create deal contexts for each offer
legalos deal add "Accel Offer"
legalos deal add "Sequoia Offer"

# Analyze each with their deal parameters
legalos analyze ./accel_termsheet.pdf --deal "Accel Offer"
legalos analyze ./sequoia_termsheet.pdf --deal "Sequoia Offer"

# Your knowledge base now has learnings from both — future analyses benefit
legalos kb search "anti-dilution"
```

---

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | Your Anthropic API key |

### Token Limits

| Setting | Value | Description |
|---------|-------|-------------|
| Single-pass limit | 150,000 tokens | Documents under this are processed in one pass |
| Max document size | 500,000 tokens | Documents over this are rejected |
| Chunk overlap | 2,000 tokens | Context preserved between chunks |

### Supported Document Types

When using `--type`, valid values are:
- `term_sheet`
- `sha` (Shareholder Agreement)
- `ssa` (Share Subscription Agreement)
- `spa` (Share Purchase Agreement)
- `convertible_note`
- `safe`

If omitted, document type is auto-detected from the content.

---

## Disclaimer

This tool provides AI-generated analysis and should not be treated as legal advice. Always have a qualified lawyer review documents before signing. LegalOS is designed to help founders understand what they're signing and identify areas that warrant closer legal review — it is not a substitute for professional legal counsel.
