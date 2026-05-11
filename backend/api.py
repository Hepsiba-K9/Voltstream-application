from typing import Literal

from fastapi import APIRouter, HTTPException, Query

from data_models import DeviceCreate, DeviceResponse, DeviceToggleResponse, EnergyDataPoint, LivePowerStatus
from mockdata import BILLING_SUMMARY, DEVICES, HISTORY, LIVE_STATUS


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
    return LIVE_STATUS


@router.get("/api/v1/analytics/history", response_model=list[EnergyDataPoint])
def get_usage_history(
    period: Literal["daily", "weekly", "monthly"] = Query(default="daily")
) -> list[EnergyDataPoint]:
    return HISTORY[period]


@router.get("/api/v1/devices", response_model=list[DeviceResponse])
def get_devices() -> list[DeviceResponse]:
    return list(DEVICES.values())


@router.post("/api/v1/devices", response_model=DeviceResponse)
def add_device(device: DeviceCreate) -> DeviceResponse:
    base_id = "".join(char.lower() for char in device.name if char.isalnum()) or "device"
    device_id = base_id
    index = 2
    while device_id in DEVICES:
        device_id = f"{base_id}-{index}"
        index += 1

    created = DeviceResponse(id=device_id, **device.model_dump())
    DEVICES[device_id] = created
    return created


@router.patch("/api/v1/devices/{device_id}", response_model=DeviceToggleResponse)
def toggle_device(device_id: str) -> DeviceToggleResponse:
    device = DEVICES.get(device_id)
    if device is None:
        raise HTTPException(status_code=404, detail="Device not found")

    updated = device.model_copy(update={"is_on": not device.is_on})
    if not updated.is_on:
        updated = updated.model_copy(update={"power_kw": 0.0})
    elif updated.power_kw == 0:
        updated = updated.model_copy(update={"power_kw": 0.9})

    DEVICES[device_id] = updated
    state = "on" if updated.is_on else "off"
    return DeviceToggleResponse(
        id=device_id,
        is_on=updated.is_on,
        message=f"{updated.name} turned {state}",
    )


@router.get("/api/v1/billing/summary")
def get_billing_summary() -> dict[str, float | int | str]:
    return BILLING_SUMMARY


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
