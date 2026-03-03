# LegalOS

AI-powered legal document analyzer for Indian startup founders navigating fundraising.

## Quick Start

```bash
pip install -e .
export ANTHROPIC_API_KEY=sk-ant-xxxxx

# Analyze a document (quick scan by default)
legalos analyze document.pdf

# Full deep analysis
legalos analyze document.pdf --deep

# Redline a Word doc with margin comments
legalos redline agreement.docx
```

## Key CLI Flags

| Flag | Description |
|------|-------------|
| `--provider` / `-p` | LLM provider: `anthropic` (default), `openai`, `google` |
| `--model` / `-m` | Model alias (`sonnet`, `opus`, `haiku`, `4o`, `pro`, etc.) or full model ID |
| `--type` | Document type: `term_sheet`, `sha`, `ssa`, `spa`, `convertible_note`, `safe` |
| `--deep` | Full 9-pass section-by-section analysis instead of quick scan |
| `--no-qa` | Skip the interactive Q&A session |
| `--no-browser` | Don't auto-open the HTML report |
| `--no-feedback` | Skip post-analysis feedback prompts |
| `--deal` | Use a named deal context |
| `--legal-brief` | Path to lawyer's notes file for this session |
| `-v` / `--verbose` | Show token usage and cost |

## Project Structure

```
src/legalos/
├── cli.py                    # Click CLI — all commands
├── config.py                 # Model mapping, pricing, API keys
├── analysis/
│   ├── client.py             # LLM clients (Anthropic, OpenAI, Gemini) + factory
│   ├── engine.py             # Analysis orchestration (quick scan + deep)
│   ├── schemas.py            # Pydantic models for analysis output
│   └── prompts/              # System/section prompts (one file per section)
├── parsing/
│   ├── router.py             # File routing (PDF/DOCX/image)
│   ├── pdf_parser.py         # PDF text extraction
│   ├── docx_parser.py        # Word document extraction
│   ├── image_parser.py       # OCR for scanned docs
│   ├── chunker.py            # Token-based document chunking
│   └── base.py               # ParsedDocument model
├── profile/
│   ├── schemas.py            # FounderProfile, DealContext, etc.
│   ├── store.py              # Profile/feedback/learnings persistence (~/.legalos/)
│   ├── init_flow.py          # Interactive profile setup
│   ├── feedback_flow.py      # Post-analysis feedback collection
│   ├── learning_capture.py   # Auto-capture insights from analyses
│   └── prompt_injection.py   # Profile → system prompt injection
├── qa/
│   └── session.py            # Interactive Q&A after analysis
├── redline/
│   └── generator.py          # DOCX margin comment generation
├── report/
│   └── generator.py          # HTML report generation
└── utils/
    ├── errors.py             # Exception hierarchy
    └── progress.py           # Rich console helpers
```

## Architecture

- **Duck-typed client pattern**: `engine.py` and `qa/session.py` receive a client and call `client.analyze()` / `client.chat()`. Any provider client works as long as it has these methods.
- **`create_client(provider, model_id, verbose)`** factory in `client.py` returns the right client.
- Profile data lives in `~/.legalos/` as JSON files.
- Reports are standalone HTML files with inline CSS/JS.

## Coding Conventions

- Python 3.10+, `from __future__ import annotations` in every file
- Pydantic v2 for all data models
- Click for CLI
- Rich for terminal output
- Lazy imports inside command functions (keeps CLI startup fast)
- No global state — everything flows through function arguments
- Tests in `tests/` directory, run with `pytest tests/ -v`
