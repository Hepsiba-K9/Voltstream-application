"""VoltStream agent tools.

All callable tool functions live here. Agent modules import tool lists from this
file and stay focused on building ADK agents.
"""

from collections.abc import Callable
from typing import Any, Literal

from ai_services.document_qa_service import retrieve_document_chunks
from data_models import DeviceCreate, DeviceResponse
from database import create_device, get_billing_summary, get_device, get_devices, get_usage_history, set_device_state

from .comments import (
    ADVISOR_AGENT_NAME,
    ANALYST_AGENT_NAME,
    ORCHESTRATOR_AGENT_NAME,
    record_tool_call,
)


Tool = Callable[..., Any]
UsagePeriod = Literal["daily", "weekly", "monthly"]

DEVICE_PAYLOAD_FIELDS = ("id", "name", "room", "type", "is_on", "power_kw")
DEVICE_TYPE_HOURS = {"climate": 56, "thermal": 21, "mobility": 14, "lighting": 35, "appliance": 10}
ENERGY_PERIODS = {"daily", "weekly", "monthly"}


def device_payload(device: DeviceResponse | None) -> dict[str, Any]:
    if device is None:
        return dict.fromkeys(DEVICE_PAYLOAD_FIELDS)
    return {field: getattr(device, field) for field in DEVICE_PAYLOAD_FIELDS}


def format_kwh(value: float) -> str:
    return f"{value:.1f} kWh"


def next_period_label(period: str) -> str:
    return {"daily": "tomorrow", "weekly": "next week", "monthly": "next month"}.get(period, "the next period")


def get_device_status(device_id: str):
    """Return the current VoltStream status for one device by ID."""
    result = device_payload(get_device(device_id))
    record_tool_call("get_device_status", {"device_id": device_id}, result)
    return result


def list_devices():
    """Return all stored VoltStream devices with IDs, names, rooms, types, states, and power draw."""
    devices = [device_payload(device) for device in get_devices()]
    result = {"devices": devices}
    record_tool_call("list_devices", {"task": "list_devices"}, {"device_count": float(len(devices))})
    return result


def toggle_device(device_id: str, state: bool):
    """Set a VoltStream device on or off and return the updated device status."""
    result = device_payload(set_device_state(device_id, state))
    record_tool_call("toggle_device", {"device_id": device_id, "state": state}, result)
    return result


def add_device(name: str, room: str, power_kw: float):
    """Add a new VoltStream device and return the created device status."""
    device_type = "Appliance"
    created = create_device(
        DeviceCreate(
            name=name.strip(),
            room=room.strip(),
            type=device_type.strip() or "Appliance",
            is_on=False,
            power_kw=max(power_kw, 0.0),
        )
    )
    result = device_payload(created)
    record_tool_call("add_device", {"name": name, "room": room, "type": device_type, "power_kw": power_kw}, result)
    return result


def _usage_period(message: str) -> UsagePeriod:
    normalized = message.lower()
    if any(term in normalized for term in ["today", "yesterday", "daily", "day", "last 24 hours"]):
        return "daily"
    if any(term in normalized for term in ["year", "yearly", "annual", "annually", "12 months", "last 12 months"]):
        return "monthly"
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
        if any(term in normalized for term in ["last year", "yearly", "annual", "annually", "12 months", "last 12 months"]):
            return "last year's"
        if "year" in normalized:
            return "yearly"
        if "last month" in normalized:
            return "last month's"
        return "this month's"
    return "selected period"


def _estimate_weekly_device_kwh(device: DeviceResponse) -> float:
    if not device.is_on or device.power_kw <= 0:
        return 0.0
    return round(device.power_kw * DEVICE_TYPE_HOURS.get(device.type.lower(), 10), 1)


def _estimate_device_kwh(device: DeviceResponse, period: str) -> float:
    weekly_estimate = _estimate_weekly_device_kwh(device)
    multipliers = {"daily": 1 / 7, "weekly": 1, "monthly": 4.33}
    return round(weekly_estimate * multipliers.get(period, 1), 1)


def analyze_usage(message: str, period: str):
    """Return usage facts for the requested period: grid, solar, net, peak, low, devices, and billing data."""
    selected_period = period.strip().lower()
    if selected_period not in ENERGY_PERIODS:
        selected_period = _usage_period(message)

    usage_history = get_usage_history(selected_period)
    devices = get_devices()
    total_grid_kwh, total_solar_kwh, total_net_kwh = (
        round(sum(getattr(point, field) for point in usage_history), 1)
        for field in ("grid_kwh", "solar_kwh", "net_kwh")
    )
    highest_point = max(usage_history, key=lambda point: point.net_kwh, default=None)
    lowest_point = min(usage_history, key=lambda point: point.net_kwh, default=None)
    device_estimates = sorted(
        [
            {**device_payload(device), "estimated_period_kwh": _estimate_device_kwh(device, selected_period)}
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
        "period": selected_period,
        "period_label": _period_label(selected_period, message),
        "next_period_label": next_period_label(selected_period),
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
        {"task": "analyze_usage", "period": selected_period},
        {
            "agent": ANALYST_AGENT_NAME,
            "period": selected_period,
            "total_grid_kwh": total_grid_kwh,
            "total_net_kwh": total_net_kwh,
            "highest_point": result["highest_point"],
        },
    )
    return result


def retrieve_advisor_rag_context(question: str):
    """Retrieve top chunks from the shared VoltSenseBot PDF Q&A RAG index."""
    chunks = retrieve_document_chunks(question, limit=3)
    record_tool_call(
        "RAG Retrieval",
        {"task": "retrieve_rag_context", "question": question},
        {
            "agent": ADVISOR_AGENT_NAME,
            "retrieved_chunks": float(len(chunks)),
            "sources": ", ".join(chunk["source"] for chunk in chunks),
        },
    )
    return chunks


def answer_energy_reference_question(question: str):
    """Answer a conceptual energy question using the shared RAG reference documents."""
    from ai_services.document_qa_service import answer_from_document

    answer, sources = answer_from_document(question)
    result = {
        "agent": ADVISOR_AGENT_NAME,
        "answer": answer,
        "sources": [
            {
                "source": source.get("source", "reference-document"),
                "chunk_id": source.get("chunk_id", ""),
            }
            for source in sources
        ],
    }
    record_tool_call(
        "Advisor Reference Answer",
        {"task": "answer_energy_reference_question", "question": question},
        {
            "agent": ADVISOR_AGENT_NAME,
            "source_count": float(len(sources)),
        },
    )
    return result


def rag_query_from_analysis(analysis: dict[str, Any]) -> str:
    period = str(analysis.get("period_label") or analysis.get("period") or "selected period")
    top_devices = [
        str(item.get("name"))
        for item in analysis.get("top_devices", [])
        if isinstance(item, dict) and float(item.get("estimated_period_kwh", 0.0)) > 0
    ]
    device_part = ", ".join(top_devices[:3]) if top_devices else "high power home devices"
    return f"energy efficiency recommendations for {device_part} during {period} usage"


def generate_recommendations(analysis: dict[str, Any]):
    """Convert usage analysis into practical savings advice."""
    rag_context = retrieve_advisor_rag_context(rag_query_from_analysis(analysis))
    recommendations: list[str] = []
    templates = {
        "climate": "Optimize {name}: raise the cooling setpoint slightly and schedule it off when rooms are empty.",
        "thermal": "Schedule {name}: heat water closer to usage time instead of keeping it on continuously.",
        "mobility": "Shift {name}: charge during solar-heavy or off-peak hours.",
    }

    for item in analysis.get("top_devices", []):
        if not isinstance(item, dict) or float(item.get("estimated_period_kwh", 0.0)) <= 0:
            continue

        device_type = str(item.get("type", "")).lower()
        name = str(item.get("name", "This device"))
        template = templates.get(
            device_type,
            "Reduce standby time for {name}: turn it off when idle and batch usage where possible.",
        )
        recommendations.append(template.format(name=name))

    if not recommendations:
        recommendations.append("Start with scheduling high-power devices and switching off idle appliances.")

    total_grid_kwh = float(analysis.get("total_grid_kwh") or 0.0)
    target_savings_kwh = round(total_grid_kwh * 0.12, 1) if total_grid_kwh > 0 else 0.0
    if target_savings_kwh:
        recommendations.append(f"A practical first target is to reduce about {format_kwh(target_savings_kwh)} {next_period_label(str(analysis.get('period') or 'weekly'))}.")

    billing = analysis.get("billing", {})
    if isinstance(billing, dict):
        projected = billing.get("projected_bill")
        budget = billing.get("budget_limit")
        if isinstance(projected, (int, float)) and isinstance(budget, (int, float)) and projected > budget:
            recommendations.append("Your projected bill is above budget, so prioritize the top active loads first.")

    result = {
        "agent": ADVISOR_AGENT_NAME,
        "recommendations": recommendations[:5],
        "target_savings_kwh": target_savings_kwh,
        "rag_context": rag_context,
    }
    record_tool_call(
        "Advisor Agent",
        {"task": "generate_energy_saving_recommendations"},
        {
            "agent": ADVISOR_AGENT_NAME,
            "recommendation_count": float(len(result["recommendations"])),
            "target_savings_kwh": target_savings_kwh,
        },
    )
    return result


def _orchestrator_agent_route(task: str, route: str) -> dict[str, str]:
    """Route the user request or analysis to the next specialist agent."""
    result = {"agent": ORCHESTRATOR_AGENT_NAME, "route": route}
    record_tool_call("Orchestrator Agent", {"task": task}, result)
    return result


def _orchestrator_agent_return_final(answer: str) -> dict[str, str | float]:
    """Record that the orchestrator prepared the final energy answer."""
    result = {"agent": ORCHESTRATOR_AGENT_NAME, "status": "final_answer_ready", "answer_length": float(len(answer))}
    record_tool_call("Orchestrator Final Response", {"task": "return_final_answer"}, result)
    return result


ENERGY_OUT_OF_SCOPE_ANSWER = (
    "I don't have that information. Please ask a question related to energy usage, solar, billing, devices, or savings."
)


def get_device_tools() -> list[Tool]:
    return [list_devices, get_device_status, toggle_device, add_device]


def get_energy_analyst_tools() -> list[Tool]:
    return [analyze_usage]


def get_energy_advisor_tools() -> list[Tool]:
    return [answer_energy_reference_question, retrieve_advisor_rag_context, generate_recommendations]


def get_orchestrator_agent_tools() -> list[Tool]:
    return get_orchestrator_tools()


def get_orchestrator_tools() -> list[Tool]:
    return []


def get_rag_tools() -> list[Tool]:
    from ai_services.document_qa_service import answer_from_document

    return [retrieve_document_chunks, answer_from_document]


def get_all_agent_tools() -> list[Tool]:
    return [
        *get_device_tools(),
        *get_energy_analyst_tools(),
        *get_energy_advisor_tools(),
        *get_orchestrator_tools(),
        *get_rag_tools(),
    ]


def get_tool_registry() -> dict[str, Tool]:
    return {tool.__name__: tool for tool in get_all_agent_tools()}
