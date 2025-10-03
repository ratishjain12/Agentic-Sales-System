"""SDR Agents module."""
from .draft_writer_agent import draft_writer_agent, create_draft_writer_agent
from .fact_checker_agent import fact_checker_agent, create_fact_checker_agent
from .proposal_generator_crew import (
    ProposalGeneratorCrew,
    proposal_generator_crew,
    generate_proposal
)

__all__ = [
    # Individual agents
    'draft_writer_agent',
    'create_draft_writer_agent',
    'fact_checker_agent',
    'create_fact_checker_agent',

    # Proposal generator crew
    'ProposalGeneratorCrew',
    'proposal_generator_crew',
    'generate_proposal',
]
