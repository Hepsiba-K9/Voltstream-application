from typing import Literal

from fastapi import APIRouter, File, HTTPException, Query, UploadFile

from ai_service import (
    AIServiceError,
    answer_from_document,
    chat_should_use_uploaded_document,
    generate_chat_response,
    generate_chat_response_from_upload,
    get_document_status,
    upload_chat_document_to_memory,
)
from data_models import (
    BillingLimitUpdate,
    BillingTrendPoint,
    ChatRequest,
    ChatResponse,
    DeviceCreate,
    DeviceResponse,
    DeviceToggleResponse,
    DocumentStatusResponse,
    EnergyDataPoint,
    LivePowerStatus,
    QARequest,
    QAResponse,
    SourceChunk,
)
from database import (
    create_device,
    get_billing_trend as fetch_billing_trend,
    get_billing_summary as fetch_billing_summary,
    get_devices as fetch_devices,
    get_live_status,
    get_usage_history as fetch_usage_history,
    toggle_device as toggle_stored_device,
    update_billing_limit as store_billing_limit,
)


router = APIRouter()


@router.get("/")
def root() -> dict[str, str]:
    return {
        "app": "VoltStream API",
        "docs": "/docs",
        "health": "/health",
    }


@router.get("/api/v1/dashboard/live", response_model=LivePowerStatus)
def get_live_dashboard() -> LivePowerStatus:
    return get_live_status()


@router.get("/api/v1/analytics/history", response_model=list[EnergyDataPoint])
def get_usage_history(
    period: Literal["daily", "weekly", "monthly"] = Query(default="daily")
) -> list[EnergyDataPoint]:
    return fetch_usage_history(period)


@router.get("/api/v1/devices", response_model=list[DeviceResponse])
def get_devices() -> list[DeviceResponse]:
    return fetch_devices()


@router.post("/api/v1/devices", response_model=DeviceResponse)
def add_device(device: DeviceCreate) -> DeviceResponse:
    return create_device(device)


@router.patch("/api/v1/devices/{device_id}", response_model=DeviceToggleResponse)
def toggle_device(device_id: str) -> DeviceToggleResponse:
    updated = toggle_stored_device(device_id)
    if updated is None:
        raise HTTPException(status_code=404, detail="Device not found")

    state = "on" if updated.is_on else "off"
    return DeviceToggleResponse(
        id=device_id,
        is_on=updated.is_on,
        message=f"{updated.name} turned {state}",
    )


@router.get("/api/v1/billing/summary")
def get_billing_summary() -> dict[str, float | int | str]:
    return fetch_billing_summary()


@router.patch("/api/v1/billing/summary")
def update_billing_summary(update: BillingLimitUpdate) -> dict[str, float | int | str]:
    if update.budget_limit <= 0:
        raise HTTPException(status_code=400, detail="Budget limit must be greater than zero")
    return store_billing_limit(update.budget_limit)


@router.get("/api/v1/billing/trend", response_model=list[BillingTrendPoint])
def get_billing_trend() -> list[BillingTrendPoint]:
    return fetch_billing_trend()


@router.post("/api/v1/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    message = request.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message is required")

    try:
        if chat_should_use_uploaded_document():
            return ChatResponse(answer=generate_chat_response_from_upload(message))
        return ChatResponse(answer=generate_chat_response(message))
    except AIServiceError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/api/v1/qa", response_model=QAResponse)
def qa(request: QARequest) -> QAResponse:
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question is required")

    try:
        answer, sources = answer_from_document(question)
        return QAResponse(
            answer=answer,
            sources=[SourceChunk(**source) for source in sources],
        )
    except AIServiceError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/api/v1/qa/document", response_model=DocumentStatusResponse)
def qa_document_status() -> DocumentStatusResponse:
    try:
        return DocumentStatusResponse(**get_document_status())
    except AIServiceError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/api/v1/chat/upload", response_model=DocumentStatusResponse)
async def upload_chat_document(file: UploadFile = File(...)) -> DocumentStatusResponse:
    if file.content_type not in {"application/pdf", "text/plain"}:
        raise HTTPException(status_code=400, detail="Upload a PDF or text document")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded document is empty")

    try:
        return DocumentStatusResponse(**upload_chat_document_to_memory(file.filename or "document.pdf", content))
    except AIServiceError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
