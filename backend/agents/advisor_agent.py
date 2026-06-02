from typing import Any

from .analyst_agent import format_kwh, next_period_label
from .comments import ADVISOR_AGENT_DESCRIPTION, ADVISOR_AGENT_INSTRUCTION, ADVISOR_AGENT_NAME, DEFAULT_MODEL, record_tool_call


def build_advisor_agent() -> Any:
    from google.adk import Agent

    return Agent(
        name=ADVISOR_AGENT_NAME,
        model=DEFAULT_MODEL,
        description=ADVISOR_AGENT_DESCRIPTION,
        instruction=ADVISOR_AGENT_INSTRUCTION,
        tools=[generate_recommendations],
    )


def generate_recommendations(analysis: dict[str, Any]) -> dict[str, Any]:
    """Advisor Agent: convert usage analysis into practical savings advice."""
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
