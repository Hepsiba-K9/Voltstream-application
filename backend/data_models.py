from pydantic import BaseModel, Field


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
    savings_today: float
    updated_at: str
    live_series: list[LivePowerSample]


class EnergyDataPoint(BaseModel):
    label: str
    grid_kwh: float
    solar_kwh: float
    net_kwh: float


class BillingTrendPoint(BaseModel):
    label: str
    current_bill: float
    projected_bill: float
    savings: float


class BillingLimitUpdate(BaseModel):
    budget_limit: float


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


class AgentRequest(BaseModel):
    message: str
    user_id: str = "voltstream-user"
    session_id: str = "voltstream-session"


class AgentToolCall(BaseModel):
    tool: str
    args: dict[str, str | bool | float]
    result: dict[str, str | bool | float | None]


class AgentResponse(BaseModel):
    answer: str
    device: DeviceResponse | None = None
    tool_calls: list[AgentToolCall] = Field(default_factory=list)
    agent_loop: list[str] = Field(default_factory=list)


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    answer: str


class QARequest(BaseModel):
    question: str


class SourceChunk(BaseModel):
    source: str
    chunk_id: str
    text: str


class QAResponse(BaseModel):
    answer: str
    sources: list[SourceChunk] = []


class DocumentStatusResponse(BaseModel):
    filename: str
    chunk_count: int
    is_default: bool
