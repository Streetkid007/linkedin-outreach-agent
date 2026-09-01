"""
Judgment step one: does this company fit Clover's thesis, is it in stealth,
and which of the four outreach profile categories does it fall into.

Source of truth for the rules below is docs/source_thesis_rules.md, pulled
from Clover_Thesis_Rules_5.2.docx on 2026-08-13. Edit that file first if the
rules change, then update this prompt to match, not the other way around.
"""

THESIS_PROMPT_TEMPLATE = """
You are screening a company for Clover, a Paris based fund investing pre
seed through Series A, selectively in later extension rounds for existing
portfolio companies.

Sectors in scope: artificial intelligence (agentic, applied, infrastructure),
productivity and future of work SaaS, fintech, B2B and B2C SaaS, edtech,
consumer health and wellbeing.

Tag out_of_scope immediately, regardless of score, if the company is
primarily: hardware or deep tech (robotics, chips), biotech or pharma
outside AI consumer health, crypto, gambling, or adult content, or a
physical D2C consumer goods brand.

Geography priority: France first, then UK, then the US, and within the US
mainly the Bay Area, New York, or Austin.

Check size: {check_size_note}

Score each of the following out of 10, multiply by its weight, average into
one weighted_score:
  market (5), team (5), founder_market_fit (2), product_or_service_viability (4),
  moat (4), business_model_and_monetization (3), legal_and_regulatory_compliance (2),
  exit_potential (3), clover_operational_edge (2), portfolio_fit (2),
  attractiveness_of_round (2), credibility_of_round (4)

Portfolio conflict: flag, do not auto exclude, if this directly competes
with an existing Clover portfolio company:
{portfolio_by_cluster}

Company data:
{company_data}

Return:
- in_scope: true or false (false if any hard exclusion applies)
- weighted_score: the computed average described above
- reason: one or two sentences, specific enough to be useful as a Pass
  Reason if in_scope is false
- portfolio_conflict: name of the conflicting portfolio company, or null
- profile_category: one of "stealth", "active_company", "high_profile",
  "warm_intro". Warm intro applies only if the source message indicates a
  mutual connection made the introduction, not just that the company is
  well known.
- language: the language outreach should be in, based on founder location
  and company language
"""

CHECK_SIZE_NOTE_CONFIRMED = (
    "100K to 200K euros, confirmed by Juliette on 2026-08-13. The 50K to "
    "150K figure in the original thesis document (v5.2) is outdated, "
    "ignore it."
)

PORTFOLIO_BY_CLUSTER = """
Enterprise AI and agents: Cominty, VibeFlow, Banana, Prior Foundry, Clarifeye
AI go to market and commerce: Get Inside, Synaps, Sillage, GetMint
Future of work, HR and talent: Pergamon, All Gravy, Linc
Health and wellbeing: Annette, Lucis
Consumer: Pally
Foundation models: Ami Labs
Edtech: Augment
Fintech: Cleavr
""".strip()


def build_prompt(company_data, check_size_note=None):
    return THESIS_PROMPT_TEMPLATE.format(
        check_size_note=check_size_note or CHECK_SIZE_NOTE_CONFIRMED,
        portfolio_by_cluster=PORTFOLIO_BY_CLUSTER,
        company_data=company_data,
    )
