"""Prompt for Plain English term explanations."""

EXPLAINER_PROMPT = """Identify the 5 most important legal terms from this document that a \
non-lawyer founder needs to understand. For each term provide:

1. definition: One sentence, plain English, under 20 words
2. real_world_example: One sentence, Indian startup context, under 25 words
3. why_it_matters: One sentence, founder perspective, under 20 words

Pick ONLY from terms actually in the document. Prioritize terms that were flagged as \
"unusual" or "aggressive" in the analysis, or that have the most founder impact. \
Keep total output under 500 tokens."""
