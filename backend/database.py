import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Literal

from data_models import (
    BillingTrendPoint,
    DeviceCreate,
    DeviceResponse,
    EnergyDataPoint,
    LivePowerSample,
    LivePowerStatus,
)


DATABASE_PATH = Path(
    os.getenv("VOLTSTREAM_DB_PATH", Path(__file__).resolve().parent / "databases" / "voltstream.sqlite3")
)
_INITIALIZED_DATABASES: set[Path] = set()


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def init_database() -> None:
    with connect() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS live_status (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                grid_draw_kw REAL NOT NULL,
                solar_generation_kw REAL NOT NULL,
                net_usage_kw REAL NOT NULL,
                battery_percent INTEGER NOT NULL,
                home_load_kw REAL NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS live_series (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                label TEXT NOT NULL,
                grid_kw REAL NOT NULL,
                solar_kw REAL NOT NULL,
                sort_order INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS usage_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                period TEXT NOT NULL,
                label TEXT NOT NULL,
                grid_kwh REAL NOT NULL,
                solar_kwh REAL NOT NULL,
                net_kwh REAL NOT NULL,
                sort_order INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS devices (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                room TEXT NOT NULL,
                type TEXT NOT NULL,
                is_on INTEGER NOT NULL,
                power_kw REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS billing_summary (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                current_balance REAL NOT NULL,
                projected_bill REAL NOT NULL,
                budget_limit REAL NOT NULL,
                billing_cycle TEXT NOT NULL,
                solar_credit REAL NOT NULL,
                days_remaining INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS billing_trend (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                label TEXT NOT NULL,
                current_bill REAL NOT NULL,
                projected_bill REAL NOT NULL,
                savings REAL NOT NULL,
                sort_order INTEGER NOT NULL
            );
            """
        )
    _INITIALIZED_DATABASES.add(DATABASE_PATH)


def ensure_database() -> None:
    if DATABASE_PATH not in _INITIALIZED_DATABASES:
        init_database()


def get_live_status() -> LivePowerStatus:
    ensure_database()
    with connect() as connection:
        status = connection.execute("SELECT * FROM live_status WHERE id = 1").fetchone()
        if status is None:
            raise ValueError("Live dashboard data is not available in the SQLite database")

        series = connection.execute(
            "SELECT label, grid_kw, solar_kw FROM live_series ORDER BY sort_order"
        ).fetchall()
        daily_solar = connection.execute(
            "SELECT COALESCE(SUM(solar_kwh), 0) AS total FROM usage_history WHERE period = 'daily'"
        ).fetchone()["total"]

    return LivePowerStatus(
        grid_draw_kw=status["grid_draw_kw"],
        solar_generation_kw=status["solar_generation_kw"],
        net_usage_kw=status["net_usage_kw"],
        battery_percent=status["battery_percent"],
        home_load_kw=status["home_load_kw"],
        savings_today=round(daily_solar * 6.5, 2),
        updated_at=status["updated_at"],
        live_series=[LivePowerSample(**dict(sample)) for sample in series],
    )


def get_usage_history(period: Literal["daily", "weekly", "monthly"]) -> list[EnergyDataPoint]:
    ensure_database()
    with connect() as connection:
        rows = connection.execute(
            """
            SELECT label, grid_kwh, solar_kwh, net_kwh
            FROM usage_history
            WHERE period = ?
            ORDER BY sort_order
            """,
            (period,),
        ).fetchall()

    return [EnergyDataPoint(**dict(row)) for row in rows]


def get_devices() -> list[DeviceResponse]:
    ensure_database()
    with connect() as connection:
        rows = connection.execute(
            "SELECT id, name, room, type, is_on, power_kw FROM devices ORDER BY name"
        ).fetchall()

    return [_device_from_row(row) for row in rows]


def get_device(device_id: str) -> DeviceResponse | None:
    ensure_database()
    with connect() as connection:
        row = connection.execute(
            "SELECT id, name, room, type, is_on, power_kw FROM devices WHERE id = ?",
            (device_id,),
        ).fetchone()

    if row is None:
        return None
    return _device_from_row(row)


def create_device(device: DeviceCreate) -> DeviceResponse:
    ensure_database()
    with connect() as connection:
        device_id = _next_device_id(connection, device.name)
        created = DeviceResponse(id=device_id, **device.model_dump())
        connection.execute(
            """
            INSERT INTO devices (id, name, room, type, is_on, power_kw)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                created.id,
                created.name,
                created.room,
                created.type,
                int(created.is_on),
                created.power_kw,
            ),
        )
        return created


def toggle_device(device_id: str) -> DeviceResponse | None:
    ensure_database()
    with connect() as connection:
        row = connection.execute(
            "SELECT id, name, room, type, is_on, power_kw FROM devices WHERE id = ?",
            (device_id,),
        ).fetchone()
        if row is None:
            return None

        device = _device_from_row(row)
        updated = device.model_copy(update={"is_on": not device.is_on})
        if not updated.is_on:
            updated = updated.model_copy(update={"power_kw": 0.0})
        elif updated.power_kw == 0:
            updated = updated.model_copy(update={"power_kw": 0.9})

        connection.execute(
            "UPDATE devices SET is_on = ?, power_kw = ? WHERE id = ?",
            (int(updated.is_on), updated.power_kw, device_id),
        )
        return updated


def set_device_state(device_id: str, state: bool) -> DeviceResponse | None:
    ensure_database()
    with connect() as connection:
        row = connection.execute(
            "SELECT id, name, room, type, is_on, power_kw FROM devices WHERE id = ?",
            (device_id,),
        ).fetchone()
        if row is None:
            return None

        device = _device_from_row(row)
        next_power_kw = device.power_kw
        if not state:
            next_power_kw = 0.0
        elif next_power_kw == 0:
            next_power_kw = 0.9

        connection.execute(
            "UPDATE devices SET is_on = ?, power_kw = ? WHERE id = ?",
            (int(state), next_power_kw, device_id),
        )

    return get_device(device_id)


def get_billing_summary() -> dict[str, float | int | str]:
    ensure_database()
    with connect() as connection:
        row = connection.execute("SELECT * FROM billing_summary WHERE id = 1").fetchone()
        if row is None:
            raise ValueError("Billing summary data is not available in the SQLite database")

    return {
        "current_balance": row["current_balance"],
        "projected_bill": row["projected_bill"],
        "budget_limit": row["budget_limit"],
        "billing_cycle": row["billing_cycle"],
        "solar_credit": row["solar_credit"],
        "days_remaining": row["days_remaining"],
    }


def update_billing_limit(budget_limit: float) -> dict[str, float | int | str]:
    ensure_database()
    with connect() as connection:
        connection.execute(
            """
            INSERT INTO billing_summary (
                id, current_balance, projected_bill, budget_limit,
                billing_cycle, solar_credit, days_remaining
            )
            VALUES (1, 0, 0, ?, '', 0, 0)
            ON CONFLICT(id) DO UPDATE SET budget_limit = excluded.budget_limit
            """,
            (budget_limit,),
        )

    return get_billing_summary()


def get_billing_trend() -> list[BillingTrendPoint]:
    ensure_database()
    with connect() as connection:
        rows = connection.execute(
            """
            SELECT label, current_bill, projected_bill, savings
            FROM billing_trend
            ORDER BY sort_order
            """
        ).fetchall()

    return [BillingTrendPoint(**dict(row)) for row in rows]


def _next_device_id(connection: sqlite3.Connection, name: str) -> str:
    base_id = "".join(char.lower() for char in name if char.isalnum()) or "device"
    device_id = base_id
    index = 2
    while _device_exists(connection, device_id):
        device_id = f"{base_id}-{index}"
        index += 1
    return device_id


def _device_exists(connection: sqlite3.Connection, device_id: str) -> bool:
    return connection.execute("SELECT 1 FROM devices WHERE id = ?", (device_id,)).fetchone() is not None


def _device_from_row(row: sqlite3.Row) -> DeviceResponse:
    values = dict(row)
    values["is_on"] = bool(values["is_on"])
    return DeviceResponse(**values)
