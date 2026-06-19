from typing import Any

from .comments import DEFAULT_MODEL, ORCHESTRATOR_AGENT_DESCRIPTION, ORCHESTRATOR_AGENT_INSTRUCTION, ORCHESTRATOR_AGENT_NAME


def build_orchestrator_agent() -> Any:
    from google.adk import Agent
    from .advisor_agent import build_advisor_agent
    from .analyst_agent import build_analyst_agent
    from .tools import get_orchestrator_agent_tools

    return Agent(
        name=ORCHESTRATOR_AGENT_NAME,
        model=DEFAULT_MODEL,
        description=ORCHESTRATOR_AGENT_DESCRIPTION,
        instruction=ORCHESTRATOR_AGENT_INSTRUCTION,
        tools=get_orchestrator_agent_tools(),
        sub_agents=[
            build_analyst_agent(),
            build_advisor_agent(),
        ],
    )
