# LegalOS

Your AI co-pilot for reviewing fundraising documents. Drop in a term sheet or SHA, get a clause-by-clause breakdown in plain English — what's standard, what's aggressive, and what to push back on.

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

## Analyzing a Document

### Get the full report

Put your document (PDF, Word, or image) somewhere you can find it, then run:

```
legalos analyze termsheet.pdf
```

Replace `termsheet.pdf` with the path to your file. For example, if it's on your Desktop:

```
legalos analyze ~/Desktop/termsheet.pdf
```

**What happens:** LegalOS reads the document, runs 8 analysis passes, and opens an interactive HTML report in your browser. After the report, it drops you into a Q&A session in the terminal where you can ask questions about the document. Type `quit` when you're done.

### Get a redlined Word document

If you have a Word (.docx) file and want margin comments with counter-proposals:

```
legalos redline sha.docx --author "Your Name"
```

This creates a new file (e.g. `sha_redlined.docx`) with comments on every clause that needs attention. You can send this directly to your lawyer or investor counsel.

### Analyze a whole folder

If you have multiple documents for the same deal (term sheet + SHA + SSA), put them in one folder and run:

```
legalos analyze ./deal-docs/
```

LegalOS will combine and analyze them together.

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
| `legalos analyze doc.pdf` | Sonnet (default) | Day-to-day analysis |
| `legalos analyze doc.pdf --model haiku` | Haiku | Quick first look, cheapest |
| `legalos analyze doc.pdf --model opus` | Opus | Final review before signing |

Add `-v` to any command to see how much a run cost.

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

**Give feedback** — tell it what it missed or over-flagged, and future analyses improve:

```
legalos feedback
```

---

## Disclaimer

LegalOS provides AI-generated analysis to help you understand what you're signing. It is not legal advice. Always have a qualified lawyer review your documents before signing.
