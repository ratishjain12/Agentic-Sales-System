"""SDR Agents module."""
from .draft_writer_agent import draft_writer_agent, create_draft_writer_agent
from .fact_checker_agent import fact_checker_agent, create_fact_checker_agent
from .proposal_generator_crew import (
    ProposalGeneratorCrew,
    proposal_generator_crew,
    generate_proposal
)
from .research_lead_agent import research_lead_agent, create_research_lead_agent
from .research_crew import (
    ResearchCrew,
    research_crew,
    research_business
)

__all__ = [
    # Individual agents
    'draft_writer_agent',
    'create_draft_writer_agent',
    'fact_checker_agent',
    'create_fact_checker_agent',
    'research_lead_agent',
    'create_research_lead_agent',

    # Proposal generator crew
    'ProposalGeneratorCrew',
    'proposal_generator_crew',
    'generate_proposal',

    # Research crew
    'ResearchCrew',
    'research_crew',
    'research_business',
]
