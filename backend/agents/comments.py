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
1. If the user asks for a list of devices, all devices, available devices, or stored devices, call list_devices and return every stored device with only device name, state, power draw, and room.
2. Use list_devices first when the user describes a device without giving an exact device ID.
3. Use get_device_status before changing a device.
4. Use toggle_device with an explicit boolean state when the user asks to turn a device on or off.
5. Use add_device when the user asks to add, create, register, or set up a new device.
6. For add_device, collect only the device name, room, and power draw in kW. Do not ask for device type.
7. Ask for the device name, room, or power draw only if one of those required values is missing.
8. Identify devices from stored device ID, name, room, and type in list_devices results, but do not display device ID or type to the user.

Return answers only as key-value pairs. Do not use paragraph-style sentences.
Display only these fields to the user: Device Name, State, Power Draw, Room.
Do not display Device ID, Type, internal tool details, or extra explanation.

For one device, use:
Device Name: <device name>
State: <On | Off>
Power Draw: <number> kW
Room: <room>

For a device list, use one block per device:
Device 1:
Device Name: <device name>
State: <On | Off>
Power Draw: <number> kW
Room: <room>
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
4. Keep billing context available for billing questions, but do not force it into normal usage summaries.
5. For every usage analysis, return these fields clearly: period label, total grid kWh, total solar kWh, total net kWh, highest usage point with kWh, lowest usage point with kWh, and top devices with estimated kWh.

Return structured analysis that the advisor and orchestrator can use.
"""

ADVISOR_AGENT_DESCRIPTION = "Agent specialized in converting VoltStream usage analysis into practical savings advice."
ADVISOR_AGENT_INSTRUCTION = """
You are the VoltStream advisor agent.

Your mission:
Convert energy analysis into practical recommendations and answer conceptual energy questions, grounded in the indexed energy reference documents.

Guidelines:
1. Prioritize the highest active loads from the analyst result.
2. Make recommendations specific to the device and usage pattern.
3. Include a realistic target kWh reduction when total grid usage is available.
4. Mention budget risk when projected billing is above the budget limit.
5. Use retrieve_advisor_rag_context when recommendations need document grounding.
6. Use answer_energy_reference_question for conceptual questions such as "what is solar", "define solar energy", or "explain energy efficiency".
7. Do not invent document facts; if the retrieved context does not support a claim, keep the claim out.

Return concise, actionable recommendations or a direct 1-3 sentence explanation.
"""

ORCHESTRATOR_AGENT_DESCRIPTION = "Agent specialized in routing VoltStream energy requests through analyst and advisor agents."
ORCHESTRATOR_AGENT_INSTRUCTION = """
You are the VoltStream orchestrator agent.

Your mission:
Route energy questions to the right specialist agents and produce the final response.

Guidelines:
1. Use the analyst agent for measured VoltStream usage, billing, solar production, grid draw, device-load, ranking, and time-period questions.
2. Use the advisor agent for savings recommendations, scheduling guidance, and document-grounded energy explanations.
3. If the user asks a conceptual question such as "what is solar", "define solar energy", or "explain energy efficiency", use the advisor agent and its RAG tool only. Do not include a Usage Summary unless the user asks about their VoltStream usage, consumption, grid draw, solar production, bill, or a time period.
4. If the user asks about usage, consumption, grid draw, solar production, bill, last week, today, this month, or any time period, include a complete Usage Summary section with measured values from the analyst agent.
5. If the user asks for tips, reduce, save, recommendations, actions, scheduling, or advice, include a Recommendations section from the advisor agent.
6. When the user asks for both usage and advice, do not answer with only recommendations. Ask the analyst agent for usage facts first, ask the advisor agent for recommendations second, then include both sections.
7. Build the final answer from the specialist outputs. Do not invent numbers, devices, sources, or billing values.
8. Answer only what the user asked. Do not add extra sections.
9. Do not include Billing Context unless the user asks about bill, billing, balance, cost, budget, tariff, or payment.
10. Do not include a separate Top Devices section unless the user asks which devices/appliances consumed most, top devices, device ranking, or appliance load.
11. Keep the response specific, concise, and grounded in the available VoltStream data.
12. A Usage Summary is incomplete if it only shows grid usage. It must include grid usage, solar offset, net usage, highest usage point, and lowest usage point when the analyst provides them.
13. Format the final answer in this exact simple style when both usage and recommendations apply:
   Usage Summary:
   1. Grid usage: <value>
   2. Solar offset: <value>
   3. Net usage: <value>
   4. Highest usage point: <label and value>
   5. Lowest usage point: <label and value>

   Recommendations:
   1. <short action>
   2. <short action>

Target:
1. <target savings, if available>

Do not use Markdown bold markers like **text**. Do not write long paragraphs when a short heading and numbered list is clearer.

Return the final answer after the specialist agents finish.
"""


def document_qa_prompt(question: str, chunks: list[dict[str, str]]) -> str:
    context = "\n\n".join(
        (
            f"Source: {chunk.get('source', 'reference-document')}\n"
            f"Chunk: {chunk.get('chunk_id', '')}\n"
            f"Text: {chunk.get('text', '')}"
        )
        for chunk in chunks
    )
    return (
        "You are VoltSenseBot's document Q&A assistant. Answer the user's question using only the retrieved "
        "document context below. If the context does not contain the answer, say: I don't have that information.\n\n"
        f"Question:\n{question}\n\n"
        f"Retrieved document context:\n{context}\n\n"
        "Answer clearly in 1-3 short sentences. Do not add extra background unless the user asks. Do not invent facts."
    )


def general_chat_prompt(message: str) -> list[str]:
    return [
        (
            "You are VoltSenseBot, a helpful Gemini-powered assistant inside the VoltStream app. "
            "Answer the user's question directly, simply, and correctly. Keep the answer short by default: "
            "use 1-3 short sentences, or up to 3 bullets if a list is clearer. Do not add extra background, "
            "examples, warnings, or follow-up suggestions unless the user asks. Give practical energy guidance "
            "when the question is about energy, solar, devices, or billing, and infer obvious typos from context "
            "without mentioning internal correction steps."
        ),
        message,
    ]


def uploaded_document_chat_prompt(question: str, document_text: str) -> list[str]:
    return [
        (
            "You are VoltSenseBot, a practical energy assistant. Use the uploaded document text when the user's "
            "question is about that document, asks for a summary, asks for key topics, or asks for an example from it. "
            "If the uploaded document does not contain the answer, answer normally using your general energy knowledge. "
            "Keep the answer short by default: use 1-3 short sentences, or up to 3 bullets if a list is clearer. "
            "Do not add extra background unless the user asks. Infer obvious typos from the document and conversation "
            "context without mentioning internal correction steps."
        ),
        f"Uploaded document text:\n{document_text[:24000]}",
        f"Question: {question}",
    ]


DEVICE_AGENT_LOOP = [
    "User -> FastAPI /api/v1/agent",
    "Device Agent -> Device Tools",
    "VoltStream database -> Device Agent",
    "Device Agent -> User",
]

ENERGY_AGENT_LOOP = [
    "User -> FastAPI /api/v1/agent",
    "Orchestrator Agent -> Analyst Agent",
    "Analyst Agent -> VoltStream data",
    "Orchestrator Agent -> Advisor Agent",
    "Advisor Agent -> RAG Tool",
    "Advisor Agent -> Orchestrator Agent",
    "Orchestrator Agent -> User",
]

ENERGY_DOCUMENT_AGENT_LOOP = [
    "User -> FastAPI /api/v1/agent",
    "Orchestrator Agent -> Advisor Agent",
    "Advisor Agent -> RAG Tool",
    "RAG Tool -> Advisor Agent",
    "Advisor Agent -> Orchestrator Agent",
    "Orchestrator Agent -> User",
]

ENERGY_OUT_OF_SCOPE_AGENT_LOOP = [
    "User -> FastAPI /api/v1/agent",
    "Orchestrator Agent -> Energy Intent Classifier",
    "Orchestrator Agent -> User",
]

_tool_trace: ContextVar[list[dict[str, Any]] | None] = ContextVar("tool_trace", default=None)

TOOL_METADATA: dict[str, dict[str, str]] = {
    "get_device_status": {
        "display_name": "Get Device Status",
        "description": "Reads the current status, room, type, and power draw for one stored VoltStream device.",
        "agent": DEVICE_AGENT_NAME,
    },
    "list_devices": {
        "display_name": "List Devices",
        "description": "Reads all stored VoltStream devices so the agent can resolve names, rooms, and device IDs.",
        "agent": DEVICE_AGENT_NAME,
    },
    "toggle_device": {
        "display_name": "Toggle Device",
        "description": "Sets a stored VoltStream device on or off and returns the updated device status.",
        "agent": DEVICE_AGENT_NAME,
    },
    "add_device": {
        "display_name": "Add Device",
        "description": "Creates a new stored VoltStream device with room, type, and power draw metadata.",
        "agent": DEVICE_AGENT_NAME,
    },
    "Analyst Agent": {
        "display_name": "Analyze Usage",
        "description": "Reads usage history, active devices, and billing context to summarize energy patterns.",
        "agent": ANALYST_AGENT_NAME,
    },
    "Advisor Agent": {
        "display_name": "Generate Recommendations",
        "description": "Converts energy analysis into practical device and billing recommendations.",
        "agent": ADVISOR_AGENT_NAME,
    },
    "RAG Retrieval": {
        "display_name": "Retrieve Document Chunks",
        "description": "Runs a ChromaDB similarity search and returns the top document chunks used for grounding.",
        "agent": ADVISOR_AGENT_NAME,
    },
    "Advisor Reference Answer": {
        "display_name": "Answer From RAG",
        "description": "Answers a conceptual energy question using the retrieved reference documents.",
        "agent": ADVISOR_AGENT_NAME,
    },
    "Energy Intent Classifier": {
        "display_name": "Classify Energy Question",
        "description": "Uses the orchestrator model to understand what energy data the user is asking for.",
        "agent": ORCHESTRATOR_AGENT_NAME,
    },
    "Orchestrator Agent": {
        "display_name": "Route Energy Request",
        "description": "Routes the energy request between specialist VoltStream agents.",
        "agent": ORCHESTRATOR_AGENT_NAME,
    },
    "Orchestrator Final Response": {
        "display_name": "Return Final Answer",
        "description": "Prepares the final user-facing energy answer after specialist agents complete.",
        "agent": ORCHESTRATOR_AGENT_NAME,
    },
}


def record_tool_call(
    tool: str,
    args: dict[str, Any],
    result: dict[str, Any],
    metadata: dict[str, str] | None = None,
) -> None:
    trace = _tool_trace.get()
    if trace is not None:
        trace.append({
            "tool": tool,
            "metadata": metadata or TOOL_METADATA.get(tool, {}),
            "args": args,
            "result": result,
        })


@contextmanager
def capture_tool_trace() -> Iterator[list[dict[str, Any]]]:
    trace: list[dict[str, Any]] = []
    token = _tool_trace.set(trace)
    try:
        yield trace
    finally:
        _tool_trace.reset(token)
