"""Analysis prompt modules."""

from legalos.analysis.prompts.system import SYSTEM_PROMPT
from legalos.analysis.prompts.control import CONTROL_PROMPT
from legalos.analysis.prompts.capital import CAPITAL_PROMPT
from legalos.analysis.prompts.investor_rights import INVESTOR_RIGHTS_PROMPT
from legalos.analysis.prompts.key_events import KEY_EVENTS_PROMPT
from legalos.analysis.prompts.founder_obligations import FOUNDER_OBLIGATIONS_PROMPT
from legalos.analysis.prompts.financial_terms import FINANCIAL_TERMS_PROMPT
from legalos.analysis.prompts.explainer import EXPLAINER_PROMPT
from legalos.analysis.prompts.impact import IMPACT_PROMPT
from legalos.analysis.prompts.redline import REDLINE_PROMPT
from legalos.analysis.prompts.executive_summary import EXECUTIVE_SUMMARY_PROMPT
from legalos.analysis.prompts.quick_scan import build_quick_scan_prompt

SECTION_PROMPTS = [
    ("control_provisions", "Control Provisions", CONTROL_PROMPT),
    ("capital_structure", "Capital Structure", CAPITAL_PROMPT),
    ("investor_rights", "Investor Rights", INVESTOR_RIGHTS_PROMPT),
    ("key_events_exit", "Key Events & Exit", KEY_EVENTS_PROMPT),
    ("founder_obligations", "Founder Obligations", FOUNDER_OBLIGATIONS_PROMPT),
    ("financial_terms", "Financial Terms", FINANCIAL_TERMS_PROMPT),
]

__all__ = [
    "SYSTEM_PROMPT",
    "SECTION_PROMPTS",
    "EXPLAINER_PROMPT",
    "IMPACT_PROMPT",
    "REDLINE_PROMPT",
    "EXECUTIVE_SUMMARY_PROMPT",
    "build_quick_scan_prompt",
]
