import inspect
import os
from typing import Any

from database import get_device

from .comments import (
    APP_NAME,
    DEVICE_AGENT_LOOP,
    ENERGY_DOCUMENT_AGENT_LOOP,
    ENERGY_AGENT_LOOP,
    ENERGY_OUT_OF_SCOPE_AGENT_LOOP,
    capture_tool_trace,
)
from .device_agent import build_device_agent
from .orchestrator_agent import build_orchestrator_agent


class AgentServiceError(RuntimeError):
    pass


_device_runner: Any | None = None
_device_session_service: Any | None = None
_energy_runner: Any | None = None
_energy_session_service: Any | None = None
_created_device_sessions: set[tuple[str, str]] = set()
_created_energy_sessions: set[tuple[str, str]] = set()


def _agent_result(answer: str, device: Any | None = None, tool_calls: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return {"answer": answer, "device": device, "tool_calls": tool_calls or []}


def _use_vertex_ai() -> bool:
    return os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "").strip().lower() in {"1", "true", "yes"}


def _ensure_google_ai_credentials() -> None:
    if _use_vertex_ai():
        project = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GOOGLE_PROJECT_ID")
        if not project:
            raise AgentServiceError("Set GOOGLE_CLOUD_PROJECT to run the ADK agent with Vertex AI.")
        os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "true")
        os.environ.setdefault("GOOGLE_CLOUD_LOCATION", os.getenv("GOOGLE_CLOUD_REGION", "us-central1"))
        return

    if not os.getenv("GOOGLE_API_KEY") and not os.getenv("GEMINI_API_KEY"):
        raise AgentServiceError(
            "Set GOOGLE_GENAI_USE_VERTEXAI=true with GOOGLE_CLOUD_PROJECT, or set GOOGLE_API_KEY/GEMINI_API_KEY."
        )
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


def _build_energy_runner() -> Any:
    try:
        from google.adk.runners import Runner
        from google.adk.sessions import InMemorySessionService
        agent = build_orchestrator_agent()
    except ImportError as exc:
        raise AgentServiceError("google-adk is not installed. Run pip install -r backend/requirements.txt.") from exc

    session_service = InMemorySessionService()
    runner = Runner(agent=agent, app_name=APP_NAME, session_service=session_service)
    return runner, session_service


async def _maybe_await(value: Any) -> Any:
    if inspect.isawaitable(value):
        return await value
    return value


async def _ensure_session(
    session_service: Any | None,
    created_sessions: set[tuple[str, str]],
    user_id: str,
    session_id: str,
) -> None:
    key = (user_id, session_id)
    if key in created_sessions or session_service is None:
        return
    await _maybe_await(session_service.create_session(app_name=APP_NAME, user_id=user_id, session_id=session_id))
    created_sessions.add(key)


def _event_text(event: Any) -> str:
    if not event.is_final_response() or not event.content or not event.content.parts:
        return ""
    return "".join(str(getattr(part, "text", "") or "") for part in event.content.parts).strip()


def _energy_agent_loop_for_trace(trace: list[dict[str, Any]]) -> list[str]:
    tools = {str(call.get("tool", "")) for call in trace}
    if "Analyst Agent" in tools:
        return ENERGY_AGENT_LOOP
    if "RAG Retrieval" in tools or "Advisor Reference Answer" in tools:
        return ENERGY_DOCUMENT_AGENT_LOOP
    if not trace:
        return ENERGY_OUT_OF_SCOPE_AGENT_LOOP
    return ENERGY_AGENT_LOOP


async def _run_device_adk_agent(message: str, user_id: str, session_id: str) -> dict[str, Any]:
    global _device_runner, _device_session_service

    _ensure_google_ai_credentials()
    if _device_runner is None or _device_session_service is None:
        _device_runner, _device_session_service = _build_device_runner()

    await _ensure_session(_device_session_service, _created_device_sessions, user_id, session_id)

    from google.genai import types

    with capture_tool_trace() as trace:
        final_answer = ""
        content = types.Content(role="user", parts=[types.Part(text=message)])
        events = _device_runner.run_async(user_id=user_id, session_id=session_id, new_message=content)
        try:
            async for event in events:
                event_text = _event_text(event)
                if event_text:
                    final_answer = event_text
        finally:
            close_events = getattr(events, "aclose", None)
            if close_events is not None:
                await close_events()

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


async def run_energy_usage_agent(message: str, user_id: str, session_id: str) -> dict[str, Any]:
    global _energy_runner, _energy_session_service

    _ensure_google_ai_credentials()
    if _energy_runner is None or _energy_session_service is None:
        _energy_runner, _energy_session_service = _build_energy_runner()

    await _ensure_session(_energy_session_service, _created_energy_sessions, user_id, session_id)

    from google.genai import types

    with capture_tool_trace() as trace:
        final_answer = ""
        content = types.Content(role="user", parts=[types.Part(text=message)])
        events = _energy_runner.run_async(user_id=user_id, session_id=session_id, new_message=content)
        try:
            async for event in events:
                event_text = _event_text(event)
                if event_text:
                    final_answer = event_text
        finally:
            close_events = getattr(events, "aclose", None)
            if close_events is not None:
                await close_events()

    return {
        "answer": final_answer or "The orchestrator completed the request.",
        "device": None,
        "tool_calls": trace,
        "agent_loop": _energy_agent_loop_for_trace(trace),
    }
