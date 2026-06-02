from typing import Any, Literal

from data_models import DeviceResponse
from database import get_billing_summary, get_devices, get_usage_history

from .comments import ANALYST_AGENT_DESCRIPTION, ANALYST_AGENT_INSTRUCTION, ANALYST_AGENT_NAME, DEFAULT_MODEL, record_tool_call


DEVICE_PAYLOAD_FIELDS = ("id", "name", "room", "type", "is_on", "power_kw")
DEVICE_TYPE_HOURS = {"climate": 56, "thermal": 21, "mobility": 14, "appliance": 10}


def build_analyst_agent() -> Any:
    from google.adk import Agent

    return Agent(
        name=ANALYST_AGENT_NAME,
        model=DEFAULT_MODEL,
        description=ANALYST_AGENT_DESCRIPTION,
        instruction=ANALYST_AGENT_INSTRUCTION,
        tools=[analyze_usage],
    )


def device_payload(device: DeviceResponse | None) -> dict[str, str | bool | float | None]:
    if device is None:
        return dict.fromkeys(DEVICE_PAYLOAD_FIELDS)
    return {field: getattr(device, field) for field in DEVICE_PAYLOAD_FIELDS}


def format_kwh(value: float) -> str:
    return f"{value:.1f} kWh"


def _usage_period(message: str) -> Literal["daily", "weekly", "monthly"]:
    normalized = message.lower()
    if any(term in normalized for term in ["today", "yesterday", "daily", "day", "last 24 hours"]):
        return "daily"
    if any(term in normalized for term in ["month", "monthly", "this month", "last month"]):
        return "monthly"
    if any(term in normalized for term in ["week", "weekly", "last week", "7 days"]):
        return "weekly"
    return "weekly"


def _period_label(period: str, message: str = "") -> str:
    normalized = message.lower()
    if period == "daily":
        if "yesterday" in normalized:
            return "yesterday's"
        if "today" in normalized:
            return "today's"
        return "daily"
    if period == "weekly":
        if "this week" in normalized:
            return "this week's"
        return "last week's"
    if period == "monthly":
        if "last month" in normalized:
            return "last month's"
        return "this month's"
    return "selected period"


def next_period_label(period: str) -> str:
    return {"daily": "tomorrow", "weekly": "next week", "monthly": "next month"}.get(period, "the next period")


def _estimate_weekly_device_kwh(device: DeviceResponse) -> float:
    if not device.is_on or device.power_kw <= 0:
        return 0.0

    return round(device.power_kw * DEVICE_TYPE_HOURS.get(device.type.lower(), 10), 1)


def _estimate_device_kwh(device: DeviceResponse, period: str) -> float:
    weekly_estimate = _estimate_weekly_device_kwh(device)
    multipliers = {"daily": 1 / 7, "weekly": 1, "monthly": 4.33}
    return round(weekly_estimate * multipliers.get(period, 1), 1)


def analyze_usage(message: str) -> dict[str, Any]:
    """Analyst Agent: read VoltStream usage data and summarize energy patterns."""
    period = _usage_period(message)
    usage_history = get_usage_history(period)
    devices = get_devices()
    total_grid_kwh, total_solar_kwh, total_net_kwh = (
        round(sum(getattr(point, field) for point in usage_history), 1)
        for field in ("grid_kwh", "solar_kwh", "net_kwh")
    )
    highest_point = max(usage_history, key=lambda point: point.net_kwh, default=None)
    lowest_point = min(usage_history, key=lambda point: point.net_kwh, default=None)
    device_estimates = sorted(
        [
            {**device_payload(device), "estimated_period_kwh": _estimate_device_kwh(device, period)}
            for device in devices
        ],
        key=lambda item: item["estimated_period_kwh"],
        reverse=True,
    )

    try:
        billing = get_billing_summary()
    except Exception:
        billing = {}

    result = {
        "agent": ANALYST_AGENT_NAME,
        "request": message,
        "period": period,
        "period_label": _period_label(period, message),
        "next_period_label": next_period_label(period),
        "total_grid_kwh": total_grid_kwh,
        "total_solar_kwh": total_solar_kwh,
        "total_net_kwh": total_net_kwh,
        "highest_point": highest_point.label if highest_point else None,
        "highest_point_net_kwh": round(highest_point.net_kwh, 1) if highest_point else None,
        "lowest_point": lowest_point.label if lowest_point else None,
        "lowest_point_net_kwh": round(lowest_point.net_kwh, 1) if lowest_point else None,
        "top_devices": device_estimates[:3],
        "billing": billing,
    }
    record_tool_call(
        "Analyst Agent",
        {"task": "analyze_usage", "period": period},
        {
            "agent": ANALYST_AGENT_NAME,
            "period": period,
            "total_grid_kwh": total_grid_kwh,
            "total_net_kwh": total_net_kwh,
            "highest_point": result["highest_point"],
        },
    )
    return result
