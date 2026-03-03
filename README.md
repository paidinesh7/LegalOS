# LegalOS

An AI-powered legal review tool for Indian startup founders navigating fundraising. Term sheets, SHAs, SSAs — every document in a fundraise has clauses that can shift control, economics, or flexibility away from founders. LegalOS helps you stay on top of all of it.

Drop in a document, get a clause-by-clause breakdown in plain English — what's standard, what's aggressive, and what to push back on. The more you use it, the better it gets at flagging what matters to you.

Built for Indian startup founders. Powered by Claude.

---

## What You Get

When you run LegalOS on a document, it produces:

- **A full HTML report** that opens in your browser — every clause explained in plain English, color-coded by severity (green = standard, orange = aggressive, red = unusual)
- **Impact scores** — how much control, economics, and flexibility you're giving up, rated 1–10
- **Negotiation priorities** — a ranked list of what to push back on, with suggested alternative language you can share with your lawyer
- **A redlined Word doc** — your document with margin comments containing counter-proposals, ready to forward to investor counsel
- **Q&A in your terminal** — after the report, you can ask follow-up questions like "What happens if we raise a down round?" or "Can they block ESOP grants?"

---

## Setup (One-Time)

You need two things: Python and an Anthropic API key.

### Step 1: Install LegalOS

Open your terminal (on Mac: search for "Terminal" in Spotlight; on Windows: use Command Prompt or PowerShell) and run:

```
pip install -e .
```

> If you have scanned PDFs or photos of documents, also run:
> ```
> pip install -e ".[ocr]"
> ```

### Step 2: Add your API key

LegalOS uses Claude (by Anthropic) to analyze documents. You'll need an API key from [console.anthropic.com](https://console.anthropic.com/).

Once you have it, run this in your terminal:

```
export ANTHROPIC_API_KEY=sk-ant-xxxxx
```

Replace `sk-ant-xxxxx` with your actual key. You'll need to do this each time you open a new terminal window, or add it to your shell profile to make it permanent.

### Step 3: Set up your profile

```
legalos init
```

This asks you two things:
1. **Your company background** — name, sector, and funding stage (e.g. Seed, Series A). This helps LegalOS tailor its analysis to your situation.
2. **Your legal team's notes** (optional) — if your lawyer has given you specific things to watch for, you can paste them in or point to a file. LegalOS will follow those instructions in every analysis.

All questions are optional — press Enter to skip any of them.

---

## Examples — Guides & Sample Reports

The `examples/` folder has everything you need to understand what LegalOS does, no API key required.

### Founder Guides

Plain-English explainers for the three core fundraising documents. Each clause is shown as a comparison table — what's standard, what's aggressive, what's unusual — with real ₹ examples and founder impact.

- **[Term Sheet Guide](examples/guide_term_sheet.html)** — valuation, liquidation preference, anti-dilution, board control, ESOP, vesting, non-compete, CPs, exclusivity
- **[SHA Guide](examples/guide_sha.html)** — board governance, reserved matters, transfer restrictions, information rights, founder obligations, exit provisions, indemnification, dispute resolution
- **[SSA Guide](examples/guide_ssa.html)** — investment mechanics (CCPS vs OCPS), conditions precedent, reps & warranties, covenants, closing mechanics

### Sample Report

1. **Open the sample report** — open `examples/sample_report.html` in your browser. This is a real analysis of a Series A term sheet.
2. **Or generate one yourself** — run `legalos analyze examples/` to analyze the sample term sheet and produce a fresh report.

Check `examples/README.md` for what to look for in the report.

---

## Analyzing a Document

### The simple way

Drop your files (PDF, Word, or images) into the `documents/` folder, then run:

```
legalos analyze
```

That's it. LegalOS picks up everything in the folder.

**What happens:** LegalOS reads the document, runs 8 analysis passes, and opens an interactive HTML report in your browser. After the report, it drops you into a Q&A session in the terminal where you can ask questions about the document. Type `quit` when you're done.

### Analyze a specific file or folder

If you prefer to specify a path explicitly:

```
legalos analyze termsheet.pdf
legalos analyze ~/Desktop/termsheet.pdf
legalos analyze ./deal-docs/
```

### Get a redlined Word document

If you have a Word (.docx) file and want margin comments with counter-proposals:

```
legalos redline sha.docx --author "Your Name"
```

This creates a new file (e.g. `sha_redlined.docx`) with comments on every clause that needs attention. You can send this directly to your lawyer or investor counsel.

---

## Tips for Better Results

**Use your lawyer's notes.** If your lawyer has sent you an email or doc with things to watch for, load it during `init` or pass it directly:

```
legalos analyze termsheet.pdf --legal-brief lawyer-notes.txt
```

**Use Opus for your final review.** The default model (Sonnet) is good for everyday use. Before you actually sign, run the analysis once more with the highest-quality model:

```
legalos analyze termsheet.pdf --model opus
```

**Specify the document type** if LegalOS gets it wrong:

```
legalos analyze document.pdf --type term_sheet
```

Valid types: `term_sheet`, `sha`, `ssa`, `spa`, `convertible_note`, `safe`

---

## Analysis Coverage

| Section | What It Looks At |
|---------|-----------------|
| **Control Provisions** | Board composition, voting rights, veto rights, reserved matters |
| **Capital Structure** | ESOP pool, anti-dilution, conversion ratios, preference shares |
| **Investor Rights** | Tag-along, drag-along, pre-emptive rights, transfer restrictions |
| **Key Events & Exit** | Liquidation preferences, exit provisions, IPO conditions, put/call options |
| **Founder Obligations** | Non-compete, lock-in, vesting, indemnification |
| **Financial Terms** | Valuation, tranches, milestones, conditions precedent |
| **Plain English Guide** | Every complex term explained with real-world Indian startup examples |
| **Impact Assessment** | Control/economics/flexibility scores, exit waterfall scenarios, negotiation priorities |

---

## Supported Files

| Format | What Works |
|--------|-----------|
| **PDF** | Regular PDFs and scanned PDFs (with OCR installed) |
| **Word (.docx)** | Preserves tables and headings |
| **Images** | PNG, JPG, TIFF — for photos of printed documents (requires OCR install) |

---

## Models & Cost

| Command | Model | When to Use |
|---------|-------|-------------|
| `legalos analyze` | Sonnet (default) | Day-to-day analysis |
| `legalos analyze --model haiku` | Haiku | Quick first look, cheapest |
| `legalos analyze --model opus` | Opus | Final review before signing |

Add `-v` to any command to see how much a run cost.

---

## Using Other AI Models

LegalOS defaults to Anthropic's Claude, but also supports OpenAI and Google Gemini models.

### Install provider support

```
pip install -e ".[openai]"     # OpenAI models
pip install -e ".[google]"     # Google Gemini models
pip install -e ".[all]"        # Both
```

### Set your API key

```
export OPENAI_API_KEY=sk-xxxxx
export GOOGLE_API_KEY=AIzaxxxxx
```

### Run with a different provider

```
legalos analyze doc.pdf --provider openai --model 4o
legalos analyze doc.pdf --provider google --model pro
legalos redline sha.docx --provider openai --model o3
```

### Available models

| Provider | Aliases | Default |
|----------|---------|---------|
| **anthropic** | `opus`, `sonnet`, `haiku` | `sonnet` |
| **openai** | `o3`, `4o`, `4o-mini` | `4o` |
| **google** | `pro`, `flash` | `flash` |

You can also pass a full model ID directly: `--model gpt-4o-2024-08-06`

> **Note:** Anthropic remains the default and best-tested provider. OpenAI and Google support is functional but less battle-tested.

---

## Power User Features

You don't need any of this to get started — but it's there when you want it.

**Update your profile** without re-running init:

```
legalos profile set risk_tolerance conservative
legalos profile set company.stage series_a
legalos profile set priorities.custom_watchlist "Full ratchet, Drag-along below 75%"
```

**Compare multiple term sheets** using deal contexts:

```
legalos deal add "Accel Offer"
legalos deal add "Sequoia Offer"
legalos analyze accel_termsheet.pdf --deal "Accel Offer"
legalos analyze sequoia_termsheet.pdf --deal "Sequoia Offer"
```

**View accumulated learnings** — LegalOS remembers insights from past analyses:

```
legalos kb
legalos kb search "anti-dilution"
```

---

## Feedback — Teaching LegalOS Your Preferences

LegalOS adapts to what matters for your deals. Every analysis ends with a quick feedback loop — tell it what it missed and what wasn't relevant, and future analyses adjust automatically. Over time, LegalOS learns your priorities so you don't have to repeat yourself.

### How to give feedback

**After every analysis** (in the terminal):

1. **Did LegalOS miss anything important?** — e.g. "Full ratchet anti-dilution, Founder vesting acceleration"
2. **Any findings that were NOT relevant?** — things it flagged that don't matter for your deal
3. **Other concerns or comments?** — free text
4. **Rate this analysis (1-5)** — quick overall rating

Type `skip` to skip the entire feedback flow. Press Enter to skip individual questions.

**From the HTML report** — click the thumbs up/down buttons on individual findings as you read, then click **Save Feedback** to copy a CLI command. Paste it in your terminal.

### What it does with your feedback

- **Missed items** get extra attention in future analyses
- **Over-flagged items** get de-emphasized unless truly unusual
- Patterns accumulate across sessions — the tool continuously sharpens to your deal context

All feedback is stored locally at `~/.legalos/feedback.json`. Nothing is uploaded anywhere.

### Quick reference

| Command | What It Does |
|---------|-------------|
| `legalos feedback` | View feedback summary — average rating, frequently missed items, over-flagged items |
| `legalos feedback import file.feedback.json` | Import per-finding feedback from an HTML report export |
| `legalos feedback submit --up "Finding 1" --down "Finding 2" --doc "doc.pdf"` | Submit feedback directly via CLI |
| `legalos feedback clear` | Delete all collected feedback |
| `legalos analyze doc.pdf --no-feedback` | Run analysis without post-analysis feedback prompts |

---

## Using Your Preferences Outside LegalOS

LegalOS generates a `MyPreferences/my_preferences.md` file that captures everything the tool knows about you — your company profile, risk tolerance, priority watchlist, accumulated learnings, and feedback patterns. This file is auto-updated every time you change your profile, give feedback, or run an analysis.

You can use this file as portable context for any AI interface:

- **Claude Projects** — upload `my_preferences.md` to a Project's knowledge base. Claude will then have your legal preferences as context when you ask it to review clauses, draft counter-proposals, or explain terms.
- **ChatGPT / Custom GPTs** — attach it as a knowledge file or paste it into a system prompt.
- **Any AI chat interface** — drop the file into the conversation as context before asking legal questions about your fundraise.

To generate or refresh the file:

```
legalos preferences
```

The file is plain Markdown — you can also edit the "Additional Notes" section at the bottom to add custom instructions that persist across regenerations.

For a more complete setup on Claude.ai, see the next section.

---

## Using LegalOS on Claude.ai

You can use the LegalOS analysis framework directly inside a Claude Project on [claude.ai](https://claude.ai) — no installation, no API key, no terminal required.

### Quick setup (no CLI)

1. Go to [claude.ai](https://claude.ai) and create a new Project
2. Open [`claude-project/instructions.md`](claude-project/instructions.md) and paste its contents into the Project's custom instructions
3. Upload these 3 files from [`claude-project/`](claude-project/) as knowledge files:
   - `analysis_checklist.md` — 6 section analysis checklists
   - `doc_type_guidance.md` — document-type emphasis areas
   - `scoring_rubric.md` — severity levels, impact scores, output formats
4. Upload your legal document (PDF or Word) and start chatting

### Personalized setup (CLI users)

If you've built up a profile, feedback patterns, and learnings in LegalOS:

```
legalos claude-export
```

This generates personalized versions of all the files in `MyPreferences/claude-project/`, including your company profile, risk tolerance, watchlist, and accumulated learnings baked into the instructions. Upload those files instead.

### What you get

The same senior Indian startup lawyer analysis framework — section checklists, severity scoring, exit waterfall, negotiation priorities — delivered conversationally inside Claude instead of as an HTML report.

---

## Disclaimer

LegalOS provides AI-generated analysis to help you understand what you're signing. It is not legal advice. Always have a qualified lawyer review your documents before signing.
