"""SDR (Sales Development Representative) module."""
from .agents import (
    # Individual agents
    draft_writer_agent,
    create_draft_writer_agent,
    fact_checker_agent,
    create_fact_checker_agent,
    research_lead_agent,
    create_research_lead_agent,
    outreach_caller_agent,
    create_outreach_caller_agent,
    conversation_classifier_agent,
    create_conversation_classifier_agent,
    lead_clerk_agent,
    create_lead_clerk_agent,
    outreach_email_agent,
    create_outreach_email_agent,

    # Proposal generator crew
    proposal_generator_crew,
    ProposalGeneratorCrew,
    generate_proposal,

    # Research crew
    research_crew,
    ResearchCrew,

    # SDR main agent (complete workflow)
    SDRAgent,
    sdr_main_agent,
    execute_sdr_main_workflow,
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
    'proposal_generator_crew',
    'ProposalGeneratorCrew',
    'generate_proposal',

    # Research crew
    'research_crew',
    'ResearchCrew',

    # SDR main agent (complete workflow)
    'SDRAgent',
    'sdr_main_agent',
    'execute_sdr_main_workflow',
]
