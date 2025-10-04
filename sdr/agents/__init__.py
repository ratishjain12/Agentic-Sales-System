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
from .outreach_caller_agent import outreach_caller_agent, create_outreach_caller_agent
from .conversation_classifier_agent import conversation_classifier_agent, create_conversation_classifier_agent
from .lead_clerk_agent import lead_clerk_agent, create_lead_clerk_agent
from .outreach_email_agent import outreach_email_agent, create_outreach_email_agent
from .sdr_main_agent import (
    SDRAgent,
    sdr_main_agent,
    execute_sdr_main_workflow
)

__all__ = [
    # Individual agents
    'draft_writer_agent',
    'create_draft_writer_agent',
    'fact_checker_agent',
    'create_fact_checker_agent',
    'research_lead_agent',
    'create_research_lead_agent',
    'outreach_caller_agent',
    'create_outreach_caller_agent',
    'conversation_classifier_agent',
    'create_conversation_classifier_agent',
    'lead_clerk_agent',
    'create_lead_clerk_agent',
    'outreach_email_agent',
    'create_outreach_email_agent',

    # Proposal generator crew
    'ProposalGeneratorCrew',
    'proposal_generator_crew',
    'generate_proposal',

    # Research crew
    'ResearchCrew',
    'research_crew',
    'research_business',

    # SDR main agent (complete workflow)
    'SDRAgent',
    'sdr_main_agent',
    'execute_sdr_main_workflow',
]
