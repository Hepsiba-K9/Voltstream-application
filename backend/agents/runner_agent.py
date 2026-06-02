import inspect
import os
from typing import Any

from database import get_device

from .advisor_agent import generate_recommendations
from .analyst_agent import analyze_usage
from .comments import (
    ADVISOR_AGENT_NAME,
    ANALYST_AGENT_NAME,
    APP_NAME,
    DEVICE_AGENT_LOOP,
    ENERGY_AGENT_LOOP,
    capture_tool_trace,
)
from .device_agent import build_device_agent
from .orchestrator_agent import _format_energy_answer, _orchestrator_agent_return_final, _orchestrator_agent_route


class AgentServiceError(RuntimeError):
    pass


_device_runner: Any | None = None
_device_session_service: Any | None = None
_created_sessions: set[tuple[str, str]] = set()


def _agent_result(answer: str, device: Any | None = None, tool_calls: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return {"answer": answer, "device": device, "tool_calls": tool_calls or []}


def _ensure_google_api_key() -> None:
    if not os.getenv("GOOGLE_API_KEY") and not os.getenv("GEMINI_API_KEY"):
        raise AgentServiceError("Set GOOGLE_API_KEY or GEMINI_API_KEY to run the ADK agent.")
    if not os.getenv("GOOGLE_API_KEY") and os.getenv("GEMINI_API_KEY"):
        os.environ["GOOGLE_API_KEY"] = os.environ["GEMINI_API_KEY"]


def _build_device_runner() -> Any:
    try:
        from google.adk.runners import Runner
        from google.adk.sessions import InMemorySessionService
        agent = build_device_agent()
    except ImportError as exc:
        raise AgentServiceError("google-adk is not installed. Run pip install -r backend/requirements.txt.") from exc

    session_service = InMemorySessionService()
    runner = Runner(agent=agent, app_name=APP_NAME, session_service=session_service)
    return runner, session_service


async def _maybe_await(value: Any) -> Any:
    if inspect.isawaitable(value):
        return await value
    return value


async def _ensure_session(user_id: str, session_id: str) -> None:
    key = (user_id, session_id)
    if key in _created_sessions or _device_session_service is None:
        return
    await _maybe_await(
        _device_session_service.create_session(app_name=APP_NAME, user_id=user_id, session_id=session_id)
    )
    _created_sessions.add(key)


async def _run_device_adk_agent(message: str, user_id: str, session_id: str) -> dict[str, Any]:
    global _device_runner, _device_session_service

    _ensure_google_api_key()
    if _device_runner is None or _device_session_service is None:
        _device_runner, _device_session_service = _build_device_runner()

    await _ensure_session(user_id, session_id)

    from google.genai import types

    with capture_tool_trace() as trace:
        final_answer = ""
        content = types.Content(role="user", parts=[types.Part(text=message)])
        events = _device_runner.run_async(user_id=user_id, session_id=session_id, new_message=content)
        async for event in events:
            if event.is_final_response() and event.content and event.content.parts:
                final_answer = "".join(part.text or "" for part in event.content.parts).strip()

    device = None
    if trace:
        last_device_id = trace[-1]["result"].get("id")
        if isinstance(last_device_id, str):
            device = get_device(last_device_id)

    return _agent_result(final_answer or "The agent completed the request.", device, trace)


async def run_device_agent(message: str, user_id: str, session_id: str) -> dict[str, Any]:
    result = await _run_device_adk_agent(message, user_id, session_id)
    result["agent_loop"] = DEVICE_AGENT_LOOP
    return result


def run_energy_usage_agent(message: str) -> dict[str, Any]:
    with capture_tool_trace() as trace:
        _orchestrator_agent_route("route_energy_usage_request", ANALYST_AGENT_NAME)
        analysis = analyze_usage(message)
        _orchestrator_agent_route("route_analysis_to_advisor", ADVISOR_AGENT_NAME)
        advice = generate_recommendations(analysis)
        answer = _format_energy_answer(message, analysis, advice)
        _orchestrator_agent_return_final(answer)

    return {
        "answer": answer,
        "device": None,
        "tool_calls": trace,
        "agent_loop": ENERGY_AGENT_LOOP,
    }
