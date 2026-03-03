# Using LegalOS on Claude.ai

Get the same analysis quality as the LegalOS CLI — directly inside a Claude Project on claude.ai. No installation, no API key, no terminal required.

---

## Quick Setup (No CLI Required)

1. **Go to [claude.ai](https://claude.ai)** and create a new Project (click Projects in the sidebar)
2. **Set custom instructions** — open `instructions.md` from this folder, copy the entire contents, and paste it into the Project's custom instructions field
3. **Upload knowledge files** — upload these 3 files to the Project's knowledge base:
   - `analysis_checklist.md` — the 6-section analysis framework
   - `doc_type_guidance.md` — term sheet / SHA / SSA emphasis areas
   - `scoring_rubric.md` — severity levels, impact scores, output formats
4. **Upload your document** — drop in your term sheet, SHA, SSA, or other fundraise document (PDF or Word)
5. **Start chatting** — Claude will analyze the document using the LegalOS framework

That's it. You'll get the same senior Indian startup lawyer analysis, delivered conversationally.

---

## Personalized Setup (CLI Users)

If you've been using LegalOS and have a profile, feedback, and learnings built up:

```bash
legalos claude-export
```

This generates personalized versions of all the files in `MyPreferences/claude-project/`. The custom instructions will include your company profile, risk tolerance, priority watchlist, feedback patterns, and accumulated learnings.

Upload these personalized files instead of the generic ones from this folder.

To refresh after giving more feedback or adding learnings:

```bash
legalos claude-export
```

---

## Tips for Best Results

- **Start with a quick scan** — upload your document and let Claude do the initial analysis. Then ask for the full deep dive on specific sections.
- **Ask follow-up questions** — "What happens if we raise a down round?", "Can they block ESOP grants?", "Is this non-compete enforceable in India?"
- **Compare documents** — upload multiple term sheets in the same Project to compare offers side by side.
- **Iterate on negotiation language** — ask Claude to draft specific counter-proposals for clauses you want to push back on.

---

## What's in Each File

| File | Purpose | Where It Goes |
|------|---------|---------------|
| `instructions.md` | Lawyer persona + analysis workflow | Project custom instructions (paste) |
| `analysis_checklist.md` | 6 detailed section checklists | Project knowledge file (upload) |
| `doc_type_guidance.md` | Document-type-specific emphasis | Project knowledge file (upload) |
| `scoring_rubric.md` | Severity, impact scores, output formats | Project knowledge file (upload) |
