from typing import Any

from .comments import ANALYST_AGENT_DESCRIPTION, ANALYST_AGENT_INSTRUCTION, ANALYST_AGENT_NAME, DEFAULT_MODEL


def build_analyst_agent() -> Any:
    from google.adk import Agent
    from .tools import get_energy_analyst_tools

    return Agent(
        name=ANALYST_AGENT_NAME,
        model=DEFAULT_MODEL,
        description=ANALYST_AGENT_DESCRIPTION,
        instruction=ANALYST_AGENT_INSTRUCTION,
        tools=get_energy_analyst_tools(),
    )
