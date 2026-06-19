from typing import Any

from .comments import ADVISOR_AGENT_DESCRIPTION, ADVISOR_AGENT_INSTRUCTION, ADVISOR_AGENT_NAME, DEFAULT_MODEL


def build_advisor_agent() -> Any:
    from google.adk import Agent
    from .tools import get_energy_advisor_tools

    return Agent(
        name=ADVISOR_AGENT_NAME,
        model=DEFAULT_MODEL,
        description=ADVISOR_AGENT_DESCRIPTION,
        instruction=ADVISOR_AGENT_INSTRUCTION,
        tools=get_energy_advisor_tools(),
    )
