from pydantic import BaseModel


class LivePowerSample(BaseModel):
    label: str
    grid_kw: float
    solar_kw: float


class LivePowerStatus(BaseModel):
    grid_draw_kw: float
    solar_generation_kw: float
    net_usage_kw: float
    battery_percent: int
    home_load_kw: float
    updated_at: str
    live_series: list[LivePowerSample]


class EnergyDataPoint(BaseModel):
    label: str
    grid_kwh: float
    solar_kwh: float
    net_kwh: float


class DeviceResponse(BaseModel):
    id: str
    name: str
    room: str
    type: str
    is_on: bool
    power_kw: float


class DeviceCreate(BaseModel):
    name: str
    room: str
    type: str = "Appliance"
    is_on: bool = False
    power_kw: float = 0.0


class DeviceToggleResponse(BaseModel):
    id: str
    is_on: bool
    message: str
