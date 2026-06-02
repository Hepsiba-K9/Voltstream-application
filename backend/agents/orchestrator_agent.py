from typing import Any

from .advisor_agent import generate_recommendations
from .analyst_agent import format_kwh, analyze_usage
from .comments import DEFAULT_MODEL, ORCHESTRATOR_AGENT_DESCRIPTION, ORCHESTRATOR_AGENT_INSTRUCTION, ORCHESTRATOR_AGENT_NAME, record_tool_call


def build_orchestrator_agent() -> Any:
    from google.adk import Agent

    return Agent(
        name=ORCHESTRATOR_AGENT_NAME,
        model=DEFAULT_MODEL,
        description=ORCHESTRATOR_AGENT_DESCRIPTION,
        instruction=ORCHESTRATOR_AGENT_INSTRUCTION,
        tools=[analyze_usage, generate_recommendations],
    )


def _orchestrator_agent_route(task: str, route: str) -> dict[str, str]:
    """Orchestrator Agent: route the user request or analysis to the next specialist agent."""
    result = {"agent": ORCHESTRATOR_AGENT_NAME, "route": route}
    record_tool_call("Orchestrator Agent", {"task": task}, result)
    return result


def _orchestrator_agent_return_final(answer: str) -> dict[str, str | float]:
    """Orchestrator Agent: return the final energy answer after specialist agents finish."""
    result = {"agent": ORCHESTRATOR_AGENT_NAME, "status": "final_answer_ready", "answer_length": float(len(answer))}
    record_tool_call("Orchestrator Final Response", {"task": "return_final_answer"}, result)
    return result


def _top_energy_devices(analysis: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        item for item in analysis.get("top_devices", [])
        if isinstance(item, dict) and float(item.get("estimated_period_kwh", 0.0)) > 0
    ]


def _format_billing_answer(analysis: dict[str, Any]) -> str:
    billing = analysis.get("billing", {})
    if not isinstance(billing, dict) or not billing:
        return "Billing data is not available right now."
    labels = [
        ("Current balance", "current_balance"),
        ("Projected bill", "projected_bill"),
        ("Budget limit", "budget_limit"),
        ("Solar credit", "solar_credit"),
        ("Days remaining", "days_remaining"),
    ]
    lines = ["Billing summary:"]
    lines.extend(f"{index}. {label}: {billing[key]}" for index, (label, key) in enumerate(labels, 1) if key in billing)
    return "\n".join(lines)


def _format_energy_answer(message: str, analysis: dict[str, Any], advice: dict[str, Any]) -> str:
    period_label = str(analysis.get("period_label") or "selected period")
    top_devices = _top_energy_devices(analysis)
    recommendations = advice.get("recommendations", [])

    lines = [
        f"{period_label.capitalize()} energy usage:",
        f"1. Grid usage: {format_kwh(float(analysis['total_grid_kwh']))}",
        f"2. Solar offset: {format_kwh(float(analysis['total_solar_kwh']))}",
        f"3. Net usage: {format_kwh(float(analysis['total_net_kwh']))}",
    ]

    for label, day_key, kwh_key in [
        ("Highest usage point", "highest_point", "highest_point_net_kwh"),
        ("Lowest usage point", "lowest_point", "lowest_point_net_kwh"),
    ]:
        if analysis.get(day_key):
            lines.append(f"{len(lines)}. {label}: {analysis[day_key]} ({format_kwh(float(analysis[kwh_key] or 0.0))})")

    if top_devices:
        lines.extend(["", "Likely largest active loads:"])
        lines.extend(
            f"{index}. {item['name']}: {format_kwh(float(item['estimated_period_kwh']))}"
            for index, item in enumerate(top_devices, start=1)
        )

    if recommendations:
        lines.extend(["", "Recommendations:"])
        lines.extend(f"{index}. {recommendation}" for index, recommendation in enumerate(recommendations, start=1))

    billing_answer = _format_billing_answer(analysis)
    if billing_answer != "Billing data is not available right now.":
        lines.extend(["", billing_answer])

    return "\n".join(lines)

