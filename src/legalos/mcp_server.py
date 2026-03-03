"""MCP tool server so Claude Code can invoke LegalOS from any project.

Usage:
    python -m legalos.mcp_server

Register in ~/.claude/settings.json:
    {
      "mcpServers": {
        "legalos": {
          "command": "python",
          "args": ["-m", "legalos.mcp_server"]
        }
      }
    }
"""

from __future__ import annotations

import json
from pathlib import Path

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("legalos")


@mcp.tool()
def analyze_document(
    path: str,
    provider: str = "anthropic",
    model: str | None = None,
    deep: bool = False,
    document_type: str = "",
) -> str:
    """Analyze a legal document (PDF, DOCX, or image) and return a JSON summary.

    Args:
        path: Path to the document file or directory.
        provider: LLM provider — "anthropic", "openai", or "google".
        model: Model alias (e.g. "sonnet", "4o", "pro") or full model ID. Defaults to provider's default.
        deep: If True, run full 9-pass section analysis. Otherwise quick scan.
        document_type: Optional document type hint: term_sheet, sha, ssa, spa, convertible_note, safe.
    """
    from legalos.analysis.client import create_client
    from legalos.config import DEFAULT_ALIAS, resolve_model
    from legalos.parsing.router import parse_input
    from legalos.profile.store import load_feedback, load_learnings, load_profile

    file_path = Path(path)
    if not file_path.exists():
        return json.dumps({"error": f"Path not found: {path}"})

    # Resolve model
    model_alias = model or DEFAULT_ALIAS[provider.lower()]
    model_id = resolve_model(model_alias, provider)

    # Parse
    try:
        documents = parse_input(file_path)
    except Exception as e:
        return json.dumps({"error": f"Parsing failed: {e}"})

    if not documents:
        return json.dumps({"error": "No supported files found."})

    # Create client
    try:
        client = create_client(provider, model_id, verbose=False)
    except (EnvironmentError, ImportError) as e:
        return json.dumps({"error": str(e)})

    # Load profile context
    profile = load_profile()
    feedback = load_feedback()
    learnings = load_learnings()

    if deep:
        from legalos.analysis.engine import run_analysis

        try:
            analysis = run_analysis(
                client, documents, profile=profile, feedback=feedback,
                document_type=document_type, learnings=learnings,
            )
        except Exception as e:
            return json.dumps({"error": f"Analysis failed: {e}"})

        return analysis.model_dump_json(indent=2)
    else:
        from legalos.analysis.engine import run_quick_analysis

        try:
            result = run_quick_analysis(
                client, documents, profile=profile, feedback=feedback,
                document_type=document_type, learnings=learnings,
            )
        except Exception as e:
            return json.dumps({"error": f"Quick scan failed: {e}"})

        return result.model_dump_json(indent=2)


@mcp.tool()
def ask_about_document(
    question: str,
    document_path: str,
    provider: str = "anthropic",
    model: str | None = None,
) -> str:
    """Ask a question about a legal document.

    Args:
        question: The question to ask about the document.
        document_path: Path to the document file.
        provider: LLM provider — "anthropic", "openai", or "google".
        model: Model alias or full model ID. Defaults to provider's default.
    """
    from legalos.analysis.client import create_client
    from legalos.config import DEFAULT_ALIAS, resolve_model
    from legalos.parsing.router import parse_input
    from legalos.profile.store import load_profile

    file_path = Path(document_path)
    if not file_path.exists():
        return f"Error: file not found: {document_path}"

    # Parse document
    try:
        documents = parse_input(file_path)
    except Exception as e:
        return f"Error parsing document: {e}"

    if not documents:
        return "No supported files found."

    combined_text = "\n\n---\n\n".join(doc.full_text for doc in documents)

    # Resolve model and create client
    model_alias = model or DEFAULT_ALIAS[provider.lower()]
    model_id = resolve_model(model_alias, provider)

    try:
        client = create_client(provider, model_id, verbose=False)
    except (EnvironmentError, ImportError) as e:
        return f"Error: {e}"

    # Build context-aware system prompt
    profile = load_profile()
    system = (
        "You are a legal analysis assistant specializing in Indian startup fundraising documents. "
        "Answer the user's question based on the document provided. "
        "Be specific, cite clauses where relevant, and explain implications for founders."
    )
    if profile and profile.company.name:
        system += f"\n\nThe user is a founder at {profile.company.name}."

    try:
        answer = client.chat(
            system_prompt=system,
            messages=[{"role": "user", "content": question}],
            document_text=combined_text,
        )
    except Exception as e:
        return f"Error: {e}"

    return answer


if __name__ == "__main__":
    mcp.run()
