from typing import Any

from data_models import DeviceCreate, DeviceResponse
from database import create_device, get_device, set_device_state

from .analyst_agent import device_payload
from .comments import record_tool_call
from .comments import (
    DEFAULT_MODEL,
    DEVICE_AGENT_DESCRIPTION,
    DEVICE_AGENT_INSTRUCTION,
    DEVICE_AGENT_NAME,
)


def _device_payload(device: DeviceResponse | None) -> dict[str, str | bool | float | None]:
    return device_payload(device)


def get_device_status(device_id: str) -> dict[str, str | bool | float | None]:
    """Return the current VoltStream status for one device by ID."""
    result = _device_payload(get_device(device_id))
    record_tool_call("get_device_status", {"device_id": device_id}, result)
    return result


def toggle_device(device_id: str, state: bool) -> dict[str, str | bool | float | None]:
    """Set a VoltStream device on or off and return the updated device status."""
    result = _device_payload(set_device_state(device_id, state))
    record_tool_call("toggle_device", {"device_id": device_id, "state": state}, result)
    return result


def add_device(name: str, room: str, device_type: str = "Appliance", power_kw: float = 0.0) -> dict[str, str | bool | float | None]:
    """Add a new VoltStream device and return the created device status."""
    created = create_device(
        DeviceCreate(name=name.strip(), room=room.strip(), type=device_type.strip() or "Appliance", is_on=False, power_kw=max(power_kw, 0.0))
    )
    result = _device_payload(created)
    record_tool_call("add_device", {"name": name, "room": room, "device_type": device_type, "power_kw": power_kw}, result)
    return result


def build_device_agent() -> Any:
    from google.adk import Agent

    return Agent(
        name=DEVICE_AGENT_NAME,
        model=DEFAULT_MODEL,
        description=DEVICE_AGENT_DESCRIPTION,
        instruction=DEVICE_AGENT_INSTRUCTION,
        tools=[get_device_status, toggle_device, add_device],
    )
