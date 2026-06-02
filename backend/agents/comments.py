from contextlib import contextmanager
from contextvars import ContextVar
import os
from typing import Any, Iterator


APP_NAME = "voltstream_device_control"
DEFAULT_MODEL = os.getenv("ADK_MODEL", "gemini-2.5-flash")
DEVICE_AGENT_NAME = "voltstream_device_agent"
ORCHESTRATOR_AGENT_NAME = "voltstream_orchestrator_agent"
ANALYST_AGENT_NAME = "voltstream_analyst_agent"
ADVISOR_AGENT_NAME = "voltstream_advisor_agent"

DEVICE_AGENT_DESCRIPTION = "Agent specialized in reading and controlling stored VoltStream devices."
DEVICE_AGENT_INSTRUCTION = """
You are the VoltStream device-control agent.

Your mission:
Safely read, add, and update devices from the VoltStream device database.

Guidelines:
1. Use get_device_status before changing a device.
2. Use toggle_device with an explicit boolean state when the user asks to turn a device on or off.
3. Use add_device when the user asks to add, create, register, or set up a new device.
4. Ask for the device name and room if either one is missing.
5. Identify devices from stored device ID, name, room, and type instead of hardcoded local aliases.

Return a concise confirmation with the updated device ID, name, state, and power draw.
"""

ANALYST_AGENT_DESCRIPTION = "Agent specialized in analyzing VoltStream usage, billing, solar, and device-load data."
ANALYST_AGENT_INSTRUCTION = """
You are the VoltStream analyst agent.

Your mission:
Turn usage history, billing context, solar production, and active device loads into clear energy insights.

Guidelines:
1. Identify the requested period: daily, weekly, or monthly.
2. Summarize grid usage, solar offset, net usage, peak point, and lowest point.
3. Estimate likely device contribution from stored device state, type, and power draw.
4. Include billing context when available.

Return structured analysis that the advisor and orchestrator can use.
"""

ADVISOR_AGENT_DESCRIPTION = "Agent specialized in converting VoltStream usage analysis into practical savings advice."
ADVISOR_AGENT_INSTRUCTION = """
You are the VoltStream advisor agent.

Your mission:
Convert energy analysis into practical recommendations that reduce grid usage and cost.

Guidelines:
1. Prioritize the highest active loads from the analyst result.
2. Make recommendations specific to the device and usage pattern.
3. Include a realistic target kWh reduction when total grid usage is available.
4. Mention budget risk when projected billing is above the budget limit.

Return concise, actionable recommendations.
"""

ORCHESTRATOR_AGENT_DESCRIPTION = "Agent specialized in routing VoltStream energy requests through analyst and advisor agents."
ORCHESTRATOR_AGENT_INSTRUCTION = """
You are the VoltStream orchestrator agent.

Your mission:
Route energy questions to the right specialist agents and produce the final response.

Guidelines:
1. Send usage, billing, solar, ranking, and recommendation requests to the analyst agent first.
2. Send analyst results to the advisor agent for savings recommendations.
3. Format the final answer based on the user's intent.
4. Keep the response specific, concise, and grounded in the available VoltStream data.

Return the final answer after the specialist agents finish.
"""

DEVICE_AGENT_LOOP = [
    "User prompt received by FastAPI /api/v1/agent",
    "VoltStream agent identifies device intent and target state",
    "Agent selects get_device_status, toggle_device, or add_device",
    "Tool reads or updates the SQLite devices table",
    "Agent observes the tool result and returns the updated status",
]

ENERGY_AGENT_LOOP = [
    "User prompt received by FastAPI /api/v1/agent",
    "Orchestrator Agent routes the request to Analyst Agent",
    "Analyst Agent reads the requested usage period, device loads, and billing context",
    "Orchestrator Agent sends the analysis to Advisor Agent",
    "Advisor Agent converts the analysis into savings recommendations",
    "Advisor Agent returns recommendations to Orchestrator Agent",
    "Orchestrator Agent returns the final usage answer",
]

_tool_trace: ContextVar[list[dict[str, Any]] | None] = ContextVar("tool_trace", default=None)


def record_tool_call(tool: str, args: dict[str, Any], result: dict[str, Any]) -> None:
    trace = _tool_trace.get()
    if trace is not None:
        trace.append({"tool": tool, "args": args, "result": result})


@contextmanager
def capture_tool_trace() -> Iterator[list[dict[str, Any]]]:
    trace: list[dict[str, Any]] = []
    token = _tool_trace.set(trace)
    try:
        yield trace
    finally:
        _tool_trace.reset(token)
