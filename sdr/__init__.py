"""SDR (Sales Development Representative) module."""
from .agents import (
    draft_writer_agent,
    fact_checker_agent,
    proposal_generator_crew,
    generate_proposal
)

__all__ = [
    'draft_writer_agent',
    'fact_checker_agent',
    'proposal_generator_crew',
    'generate_proposal',
]
