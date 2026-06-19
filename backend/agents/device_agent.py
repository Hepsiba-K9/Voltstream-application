from typing import Any

from .comments import (
    DEFAULT_MODEL,
    DEVICE_AGENT_DESCRIPTION,
    DEVICE_AGENT_INSTRUCTION,
    DEVICE_AGENT_NAME,
)


def build_device_agent() -> Any:
    from google.adk import Agent
    from .tools import get_device_tools

    return Agent(
        name=DEVICE_AGENT_NAME,
        model=DEFAULT_MODEL,
        description=DEVICE_AGENT_DESCRIPTION,
        instruction=DEVICE_AGENT_INSTRUCTION,
        tools=get_device_tools(),
    )
