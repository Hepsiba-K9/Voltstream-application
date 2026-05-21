import inspect
import os
import re
from contextvars import ContextVar
from typing import Any

from data_models import DeviceCreate, DeviceResponse
from database import create_device, get_device, get_devices, set_device_state


APP_NAME = "voltstream_device_control"
AGENT_NAME = "voltstream_device_agent"
DEFAULT_MODEL = os.getenv("ADK_MODEL", "gemini-2.5-flash")

_tool_trace: ContextVar[list[dict[str, Any]] | None] = ContextVar("tool_trace", default=None)
_runner: Any | None = None
_session_service: Any | None = None
_created_sessions: set[tuple[str, str]] = set()


class AgentServiceError(RuntimeError):
    pass


def _device_payload(device: DeviceResponse | None) -> dict[str, str | bool | float | None]:
    if device is None:
        return {
            "id": None,
            "name": None,
            "room": None,
            "type": None,
            "is_on": None,
            "power_kw": None,
        }
    return {
        "id": device.id,
        "name": device.name,
        "room": device.room,
        "type": device.type,
        "is_on": device.is_on,
        "power_kw": device.power_kw,
    }


def _record_tool_call(tool: str, args: dict[str, str | bool | float], result: dict[str, Any]) -> None:
    trace = _tool_trace.get()
    if trace is not None:
        trace.append({"tool": tool, "args": args, "result": result})


def get_device_status(device_id: str) -> dict[str, str | bool | float | None]:
    """Return the current VoltStream status for one device by ID."""
    result = _device_payload(get_device(device_id))
    _record_tool_call("get_device_status", {"device_id": device_id}, result)
    return result


def toggle_device(device_id: str, state: bool) -> dict[str, str | bool | float | None]:
    """Set a VoltStream device on or off and return the updated device status."""
    result = _device_payload(set_device_state(device_id, state))
    _record_tool_call("toggle_device", {"device_id": device_id, "state": state}, result)
    return result


def add_device(name: str, room: str, device_type: str = "Appliance", power_kw: float = 0.0) -> dict[str, str | bool | float | None]:
    """Add a new VoltStream device and return the created device status."""
    created = create_device(
        DeviceCreate(
            name=name.strip(),
            room=room.strip(),
            type=device_type.strip() or "Appliance",
            is_on=False,
            power_kw=max(power_kw, 0.0),
        )
    )
    result = _device_payload(created)
    _record_tool_call(
        "add_device",
        {"name": name, "room": room, "device_type": device_type, "power_kw": power_kw},
        result,
    )
    return result


def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _contains_phrase(message: str, phrase: str) -> bool:
    normalized_phrase = _normalize(phrase)
    if not normalized_phrase:
        return False
    return f" {normalized_phrase} " in f" {message} "


def _resolve_device_id(message: str) -> str | None:
    devices = get_devices()
    normalized_message = _normalize(message)

    aliases = {
        "air conditioning": ["hvac", "ac", "air conditioner", "air conditioning", "cooling"],
        "ac": ["hvac", "ac", "air conditioner", "air conditioning", "cooling"],
        "hvac": ["hvac", "ac", "air conditioner", "air conditioning", "cooling"],
        "charger": ["charger", "ev charger"],
        "washer": ["washer", "washing machine", "smart washer"],
        "heater": ["heater", "water heater"],
    }

    for device in devices:
        candidates = {device.id, device.name, device.room, device.type}
        for key, values in aliases.items():
            if key in _normalize(f"{device.id} {device.name}"):
                candidates.update(values)

        if any(_contains_phrase(normalized_message, candidate) for candidate in candidates):
            return device.id

    return devices[0].id if len(devices) == 1 else None


def _requested_state(message: str) -> bool | None:
    normalized = _normalize(message)
    if any(phrase in normalized for phrase in ["turn off", "switch off", "power off", "shut off", "disable", "off"]):
        return False
    if any(phrase in normalized for phrase in ["turn on", "switch on", "power on", "enable", "on"]):
        return True
    return None


def _is_add_device_request(message: str) -> bool:
    normalized = _normalize(message)
    return any(
        _contains_phrase(normalized, phrase)
        for phrase in ["add", "create", "register", "new device", "setup", "set up"]
    )


def _title_device_name(value: str) -> str:
    words = [word for word in _normalize(value).split() if word not in {"a", "an", "the", "new", "device"}]
    return " ".join(word.capitalize() for word in words)


def _infer_device_type(name: str) -> str:
    normalized = _normalize(name)
    if any(word in normalized for word in ["ac", "air conditioner", "air conditioning", "hvac", "fan", "cooler"]):
        return "Climate"
    if any(word in normalized for word in ["heater", "geyser"]):
        return "Thermal"
    if any(word in normalized for word in ["charger", "ev"]):
        return "Mobility"
    return "Appliance"


def _extract_new_device(message: str) -> dict[str, str | float] | None:
    text = _normalize(message)
    patterns = [
        r"^(?:add|create|register|setup|set up)\s+(?:a\s+|an\s+|the\s+)?(?P<name>.+?)\s+(?:in|to|for)\s+(?:the\s+)?(?P<room>.+)$",
        r"^(?:add|create|register)\s+(?:a\s+|an\s+|the\s+)?(?:new\s+)?device\s+(?:called|named)\s+(?P<name>.+?)\s+(?:in|to|for)\s+(?:the\s+)?(?P<room>.+)$",
    ]

    for pattern in patterns:
        match = re.match(pattern, text)
        if not match:
            continue

        name = _title_device_name(match.group("name"))
        room = _title_device_name(match.group("room"))
        if not name or not room:
            return None
        return {
            "name": name,
            "room": room,
            "device_type": _infer_device_type(name),
            "power_kw": 0.0,
        }

    return None


def _format_status(device: DeviceResponse) -> str:
    state = "on" if device.is_on else "off"
    return f"{device.name} is {state}. Device ID: {device.id}. Current draw: {device.power_kw} kW."


def _fallback_agent_response(message: str) -> dict[str, Any]:
    if _is_add_device_request(message):
        new_device = _extract_new_device(message)
        if new_device is None:
            return {
                "answer": "Tell me the device name and room. For example: Add a ceiling fan in bedroom.",
                "device": None,
                "tool_calls": [],
            }

        trace: list[dict[str, Any]] = []
        token = _tool_trace.set(trace)
        try:
            created_payload = add_device(**new_device)
            created = get_device(str(created_payload["id"]))
        finally:
            _tool_trace.reset(token)

        if created is None:
            return {
                "answer": "I could not add that device.",
                "device": None,
                "tool_calls": trace,
            }
        return {
            "answer": f"Added {created.name} in {created.room}.",
            "device": created,
            "tool_calls": trace,
        }

    device_id = _resolve_device_id(message)
    if device_id is None:
        available = ", ".join(f"{device.name} ({device.id})" for device in get_devices())
        return {
            "answer": f"I could not confidently identify the device. Available devices: {available}.",
            "device": None,
            "tool_calls": [],
        }

    trace: list[dict[str, Any]] = []
    token = _tool_trace.set(trace)
    try:
        current = get_device_status(device_id)
        state = _requested_state(message)
        if state is None:
            device = get_device(device_id)
            answer = _format_status(device) if device else "Device not found."
            return {"answer": answer, "device": device, "tool_calls": trace}

        updated_payload = toggle_device(device_id, state)
        updated = get_device(device_id)
    finally:
        _tool_trace.reset(token)

    if updated is None or updated_payload["id"] is None:
        answer = f"Device '{device_id}' was not found."
    else:
        action = "on" if state else "off"
        answer = f"Done. I turned {action} {updated.name}. Updated status: {_format_status(updated)}"

    return {"answer": answer, "device": updated, "tool_calls": trace}


def _build_agent() -> Any:
    try:
        from google.adk import Agent
        from google.adk.runners import Runner
        from google.adk.sessions import InMemorySessionService
    except ImportError as exc:
        raise AgentServiceError("google-adk is not installed. Run pip install -r backend/requirements.txt.") from exc

    agent = Agent(
        name=AGENT_NAME,
        model=DEFAULT_MODEL,
        instruction=(
            "You are the VoltStream device-control agent. "
            "Use get_device_status before changing a device. "
            "Use toggle_device with an explicit boolean state when the user asks to turn a device on or off. "
            "Use add_device when the user asks to add, create, register, or set up a new device. "
            "Ask for the device name and room if either one is missing. "
            "Map Air Conditioning, AC, cooling, and HVAC to the hvac device when available. "
            "Return a concise confirmation with the updated device ID, name, state, and power draw."
        ),
        tools=[get_device_status, toggle_device, add_device],
    )
    session_service = InMemorySessionService()
    runner = Runner(agent=agent, app_name=APP_NAME, session_service=session_service)
    return runner, session_service


async def _maybe_await(value: Any) -> Any:
    if inspect.isawaitable(value):
        return await value
    return value


async def _ensure_session(user_id: str, session_id: str) -> None:
    key = (user_id, session_id)
    if key in _created_sessions or _session_service is None:
        return
    await _maybe_await(
        _session_service.create_session(app_name=APP_NAME, user_id=user_id, session_id=session_id)
    )
    _created_sessions.add(key)


async def _run_adk_agent(message: str, user_id: str, session_id: str) -> dict[str, Any]:
    global _runner, _session_service

    if not os.getenv("GOOGLE_API_KEY") and not os.getenv("GEMINI_API_KEY"):
        raise AgentServiceError("Set GOOGLE_API_KEY or GEMINI_API_KEY to run the ADK agent.")
    if not os.getenv("GOOGLE_API_KEY") and os.getenv("GEMINI_API_KEY"):
        os.environ["GOOGLE_API_KEY"] = os.environ["GEMINI_API_KEY"]

    if _runner is None or _session_service is None:
        _runner, _session_service = _build_agent()

    await _ensure_session(user_id, session_id)

    from google.genai import types

    trace: list[dict[str, Any]] = []
    token = _tool_trace.set(trace)
    final_answer = ""
    try:
        content = types.Content(role="user", parts=[types.Part(text=message)])
        events = _runner.run_async(user_id=user_id, session_id=session_id, new_message=content)
        async for event in events:
            if event.is_final_response() and event.content and event.content.parts:
                final_answer = "".join(part.text or "" for part in event.content.parts).strip()
    finally:
        _tool_trace.reset(token)

    device = None
    if trace:
        last_device_id = trace[-1]["result"].get("id")
        if isinstance(last_device_id, str):
            device = get_device(last_device_id)

    return {
        "answer": final_answer or "The agent completed the request.",
        "device": device,
        "tool_calls": trace,
    }


async def run_device_agent(message: str, user_id: str, session_id: str) -> dict[str, Any]:
    if _is_add_device_request(message) or _resolve_device_id(message) is not None:
        result = _fallback_agent_response(message)
    else:
        try:
            result = await _run_adk_agent(message, user_id, session_id)
        except Exception:
            result = _fallback_agent_response(message)

    result["agent_loop"] = [
        "User prompt received by FastAPI /api/v1/agent",
        "VoltStream agent identifies device intent and target state",
        "Agent selects get_device_status, toggle_device, or add_device",
        "Tool reads or updates the SQLite devices table",
        "Agent observes the tool result and returns the updated status",
    ]
    return result
