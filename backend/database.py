import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, Literal

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
DATABASE_ENGINE = os.getenv("DATABASE_ENGINE", "").strip().lower()
MYSQL_HOST = os.getenv("MYSQL_HOST", "").strip()
CLOUD_SQL_CONNECTION_NAME = (
    os.getenv("CLOUD_SQL_CONNECTION_NAME", "").strip()
    or os.getenv("INSTANCE_CONNECTION_NAME", "").strip()
)
MYSQL_UNIX_SOCKET = os.getenv("MYSQL_UNIX_SOCKET", "").strip()
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", os.getenv("MYSQL_DB", "")).strip()
MYSQL_USER = os.getenv("MYSQL_USER", "").strip()
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "").strip()
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
RUNNING_ON_CLOUD_RUN = bool(os.getenv("K_SERVICE"))

if MYSQL_UNIX_SOCKET and not MYSQL_UNIX_SOCKET.startswith("/cloudsql/"):
    MYSQL_UNIX_SOCKET = f"/cloudsql/{MYSQL_UNIX_SOCKET}"
elif CLOUD_SQL_CONNECTION_NAME and not MYSQL_UNIX_SOCKET:
    MYSQL_UNIX_SOCKET = f"/cloudsql/{CLOUD_SQL_CONNECTION_NAME}"

USE_MYSQL = DATABASE_ENGINE == "mysql" or bool(MYSQL_HOST or MYSQL_UNIX_SOCKET)
if RUNNING_ON_CLOUD_RUN and not USE_MYSQL:
    raise RuntimeError(
        "Cloud Run is running without Cloud SQL configuration. "
        "Set DATABASE_ENGINE=mysql and CLOUD_SQL_CONNECTION_NAME or MYSQL_UNIX_SOCKET."
    )

_INITIALIZED_DATABASES: set[str] = set()

DEVICE_POWER_DEFAULTS = {
    "aircooler": 1.2,
    "ceilingfan": 0.08,
    "charger": 7.2,
    "hvac": 3.4,
    "offan": 0.08,
    "washer": 0.6,
    "heater": 4.5,
}

SEED_LIVE_STATUS = {
    "id": 1,
    "grid_draw_kw": 2.5,
    "solar_generation_kw": 4.8,
    "net_usage_kw": -2.3,
    "battery_percent": 76,
    "home_load_kw": 2.4,
    "updated_at": "2026-05-06T10:15:00+05:30",
}

SEED_LIVE_SERIES = [
    ("6 AM", 5.0, 0.2, 0),
    ("9 AM", 4.1, 3.2, 1),
    ("12 PM", 2.2, 4.9, 2),
    ("3 PM", 1.5, 4.6, 3),
    ("6 PM", 3.8, 2.5, 4),
    ("9 PM", 5.2, 0.1, 5),
]

SEED_USAGE_HISTORY = [
    ("daily", "6 AM", 0.8, 0.2, 0.6, 0),
    ("daily", "9 AM", 1.1, 2.7, -1.6, 1),
    ("daily", "12 PM", 0.4, 5.1, -4.7, 2),
    ("daily", "3 PM", 0.7, 4.3, -3.6, 3),
    ("daily", "6 PM", 2.8, 0.9, 1.9, 4),
    ("daily", "9 PM", 3.2, 0.0, 3.2, 5),
    ("weekly", "Mon", 16.0, 28.0, -12.0, 0),
    ("weekly", "Tue", 18.0, 25.0, -7.0, 1),
    ("weekly", "Wed", 14.0, 31.0, -17.0, 2),
    ("weekly", "Thu", 19.0, 23.0, -4.0, 3),
    ("weekly", "Fri", 22.0, 20.0, 2.0, 4),
    ("weekly", "Sat", 25.0, 26.0, -1.0, 5),
    ("weekly", "Sun", 17.0, 30.0, -13.0, 6),
    ("monthly", "Jan", 118.0, 154.0, -36.0, 0),
    ("monthly", "Feb", 126.0, 166.0, -40.0, 1),
    ("monthly", "Mar", 132.0, 184.0, -52.0, 2),
    ("monthly", "Apr", 141.0, 193.0, -52.0, 3),
    ("monthly", "May", 148.0, 205.0, -57.0, 4),
    ("monthly", "Jun", 152.0, 214.0, -62.0, 5),
    ("monthly", "Jul", 158.0, 221.0, -63.0, 6),
    ("monthly", "Aug", 149.0, 208.0, -59.0, 7),
    ("monthly", "Sep", 142.0, 194.0, -52.0, 8),
    ("monthly", "Oct", 136.0, 176.0, -40.0, 9),
    ("monthly", "Nov", 128.0, 162.0, -34.0, 10),
    ("monthly", "Dec", 121.0, 150.0, -29.0, 11),
]

SEED_DEVICES = [
    ("hvac", "Living Room HVAC", "Living Room", "Climate", 1, 3.4),
    ("charger", "EV Charger", "Garage", "Mobility", 1, 7.2),
    ("washer", "Smart Washer", "Utility", "Appliance", 1, 0.6),
    ("heater", "Water Heater", "Basement", "Thermal", 1, 4.5),
    ("ceilingfan", "Ceiling Fan", "Bedroom", "Climate", 1, 0.08),
    ("aircooler", "Air Cooler", "Hall", "Climate", 0, 0.0),
    ("offan", "Of Fan", "Hall", "Climate", 1, 0.08),
    ("ac", "Ac", "Hall", "Climate", 1, 3.4),
    ("light", "Light", "Hall", "Lighting", 0, 0.06),
]

SEED_BILLING_SUMMARY = {
    "id": 1,
    "current_balance": 48.62,
    "projected_bill": 152.4,
    "budget_limit": 50999.0,
    "billing_cycle": "May 2026",
    "solar_credit": 28.15,
    "days_remaining": 14,
}

SEED_BILLING_TREND = [
    ("Jan", 68.0, 82.0, 42.0, 0),
    ("Feb", 74.0, 90.0, 46.0, 1),
    ("Mar", 82.0, 98.0, 58.0, 2),
    ("Apr", 78.0, 91.0, 52.0, 3),
    ("May", 95.0, 116.0, 61.0, 4),
    ("Jun", 92.0, 110.0, 64.0, 5),
    ("Jul", 104.0, 124.0, 70.0, 6),
    ("Aug", 99.0, 118.0, 66.0, 7),
    ("Sep", 88.0, 105.0, 59.0, 8),
    ("Oct", 91.0, 109.0, 55.0, 9),
    ("Nov", 108.0, 129.0, 62.0, 10),
    ("Dec", 116.0, 138.0, 68.0, 11),
]


def _database_key() -> str:
    if USE_MYSQL:
        return f"mysql:{MYSQL_UNIX_SOCKET or MYSQL_HOST}:{MYSQL_DATABASE}"
    return f"sqlite:{DATABASE_PATH}"


def get_database_connection_status() -> dict[str, str | bool]:
    if USE_MYSQL:
        connection_type = "cloud_sql_unix_socket" if MYSQL_UNIX_SOCKET else "mysql_public_ip"
        target = MYSQL_UNIX_SOCKET or f"{MYSQL_HOST}:{MYSQL_PORT}"
        return {
            "engine": "mysql",
            "connection_type": connection_type,
            "database": MYSQL_DATABASE,
            "target": target,
            "running_on_cloud_run": RUNNING_ON_CLOUD_RUN,
        }

    return {
        "engine": "sqlite",
        "connection_type": "local_file",
        "database": str(DATABASE_PATH),
        "target": str(DATABASE_PATH),
        "running_on_cloud_run": RUNNING_ON_CLOUD_RUN,
    }


def _placeholder(sql: str) -> str:
    return sql.replace("?", "%s") if USE_MYSQL else sql


def _row_to_dict(row: Any) -> dict[str, Any]:
    return dict(row)


@contextmanager
def connect() -> Iterator[Any]:
    if USE_MYSQL:
        try:
            import pymysql
            from pymysql.cursors import DictCursor
        except ImportError as exc:
            raise RuntimeError("Install PyMySQL to use Cloud SQL MySQL: pip install PyMySQL") from exc

        if not MYSQL_DATABASE or not MYSQL_USER:
            raise RuntimeError("Set MYSQL_DATABASE and MYSQL_USER before using MySQL.")

        options: dict[str, Any] = {
            "user": MYSQL_USER,
            "password": MYSQL_PASSWORD,
            "database": MYSQL_DATABASE,
            "cursorclass": DictCursor,
            "autocommit": False,
        }
        if MYSQL_UNIX_SOCKET:
            options["unix_socket"] = MYSQL_UNIX_SOCKET
        else:
            options["host"] = MYSQL_HOST or "127.0.0.1"
            options["port"] = MYSQL_PORT

        connection = pymysql.connect(**options)
    else:
        DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(DATABASE_PATH)
        connection.row_factory = sqlite3.Row

    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def _execute(connection: Any, sql: str, params: tuple[Any, ...] = ()) -> Any:
    cursor = connection.cursor()
    cursor.execute(_placeholder(sql), params)
    return cursor


def _executemany(connection: Any, sql: str, rows: list[tuple[Any, ...]]) -> None:
    cursor = connection.cursor()
    cursor.executemany(_placeholder(sql), rows)


def _fetchone(connection: Any, sql: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
    row = _execute(connection, sql, params).fetchone()
    return _row_to_dict(row) if row is not None else None


def _fetchall(connection: Any, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    return [_row_to_dict(row) for row in _execute(connection, sql, params).fetchall()]


def init_database() -> None:
    with connect() as connection:
        if USE_MYSQL:
            _init_mysql_database(connection)
        else:
            _init_sqlite_database(connection)
        _seed_database(connection)
    _INITIALIZED_DATABASES.add(_database_key())


def _init_sqlite_database(connection: Any) -> None:
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


def _init_mysql_database(connection: Any) -> None:
    statements = [
        """
        CREATE TABLE IF NOT EXISTS live_status (
            id INT PRIMARY KEY,
            grid_draw_kw DOUBLE NOT NULL,
            solar_generation_kw DOUBLE NOT NULL,
            net_usage_kw DOUBLE NOT NULL,
            battery_percent INT NOT NULL,
            home_load_kw DOUBLE NOT NULL,
            updated_at VARCHAR(64) NOT NULL,
            CHECK (id = 1)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS live_series (
            id INT AUTO_INCREMENT PRIMARY KEY,
            label VARCHAR(64) NOT NULL,
            grid_kw DOUBLE NOT NULL,
            solar_kw DOUBLE NOT NULL,
            sort_order INT NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS usage_history (
            id INT AUTO_INCREMENT PRIMARY KEY,
            period VARCHAR(16) NOT NULL,
            label VARCHAR(64) NOT NULL,
            grid_kwh DOUBLE NOT NULL,
            solar_kwh DOUBLE NOT NULL,
            net_kwh DOUBLE NOT NULL,
            sort_order INT NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS devices (
            id VARCHAR(128) PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            room VARCHAR(255) NOT NULL,
            type VARCHAR(128) NOT NULL,
            is_on TINYINT(1) NOT NULL,
            power_kw DOUBLE NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS billing_summary (
            id INT PRIMARY KEY,
            current_balance DOUBLE NOT NULL,
            projected_bill DOUBLE NOT NULL,
            budget_limit DOUBLE NOT NULL,
            billing_cycle VARCHAR(64) NOT NULL,
            solar_credit DOUBLE NOT NULL,
            days_remaining INT NOT NULL,
            CHECK (id = 1)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS billing_trend (
            id INT AUTO_INCREMENT PRIMARY KEY,
            label VARCHAR(64) NOT NULL,
            current_bill DOUBLE NOT NULL,
            projected_bill DOUBLE NOT NULL,
            savings DOUBLE NOT NULL,
            sort_order INT NOT NULL
        )
        """,
    ]
    for statement in statements:
        _execute(connection, statement)


def _seed_database(connection: Any) -> None:
    if _table_count(connection, "live_status") == 0:
        _execute(
            connection,
            """
            INSERT INTO live_status (
                id, grid_draw_kw, solar_generation_kw, net_usage_kw,
                battery_percent, home_load_kw, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            tuple(SEED_LIVE_STATUS.values()),
        )

    if _table_count(connection, "live_series") == 0:
        _executemany(
            connection,
            "INSERT INTO live_series (label, grid_kw, solar_kw, sort_order) VALUES (?, ?, ?, ?)",
            SEED_LIVE_SERIES,
        )

    if _table_count(connection, "usage_history") == 0:
        _executemany(
            connection,
            """
            INSERT INTO usage_history (period, label, grid_kwh, solar_kwh, net_kwh, sort_order)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            SEED_USAGE_HISTORY,
        )

    if _table_count(connection, "devices") == 0:
        _executemany(
            connection,
            "INSERT INTO devices (id, name, room, type, is_on, power_kw) VALUES (?, ?, ?, ?, ?, ?)",
            SEED_DEVICES,
        )

    if _table_count(connection, "billing_summary") == 0:
        _execute(
            connection,
            """
            INSERT INTO billing_summary (
                id, current_balance, projected_bill, budget_limit,
                billing_cycle, solar_credit, days_remaining
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            tuple(SEED_BILLING_SUMMARY.values()),
        )

    if _table_count(connection, "billing_trend") == 0:
        _executemany(
            connection,
            """
            INSERT INTO billing_trend (label, current_bill, projected_bill, savings, sort_order)
            VALUES (?, ?, ?, ?, ?)
            """,
            SEED_BILLING_TREND,
        )


def _table_count(connection: Any, table_name: str) -> int:
    row = _fetchone(connection, f"SELECT COUNT(*) AS total FROM {table_name}")
    return int(row["total"]) if row else 0


def ensure_database() -> None:
    if _database_key() not in _INITIALIZED_DATABASES:
        init_database()


def get_live_status() -> LivePowerStatus:
    ensure_database()
    with connect() as connection:
        status = _fetchone(connection, "SELECT * FROM live_status WHERE id = 1")
        if status is None:
            raise ValueError("Live dashboard data is not available in the database")

        series = _fetchall(connection, "SELECT label, grid_kw, solar_kw FROM live_series ORDER BY sort_order")
        daily_solar = _fetchone(
            connection,
            "SELECT COALESCE(SUM(solar_kwh), 0) AS total FROM usage_history WHERE period = 'daily'",
        )["total"]

    return LivePowerStatus(
        grid_draw_kw=status["grid_draw_kw"],
        solar_generation_kw=status["solar_generation_kw"],
        net_usage_kw=status["net_usage_kw"],
        battery_percent=status["battery_percent"],
        home_load_kw=status["home_load_kw"],
        savings_today=round(float(daily_solar) * 6.5, 2),
        updated_at=status["updated_at"],
        live_series=[LivePowerSample(**sample) for sample in series],
    )


def get_usage_history(period: Literal["daily", "weekly", "monthly"]) -> list[EnergyDataPoint]:
    ensure_database()
    with connect() as connection:
        rows = _fetchall(
            connection,
            """
            SELECT label, grid_kwh, solar_kwh, net_kwh
            FROM usage_history
            WHERE period = ?
            ORDER BY sort_order
            """,
            (period,),
        )

    return [EnergyDataPoint(**row) for row in rows]


def get_devices() -> list[DeviceResponse]:
    ensure_database()
    normalize_device_power_defaults()
    with connect() as connection:
        rows = _fetchall(connection, "SELECT id, name, room, type, is_on, power_kw FROM devices ORDER BY name")

    return [_device_from_row(row) for row in rows]


def get_device(device_id: str) -> DeviceResponse | None:
    ensure_database()
    with connect() as connection:
        row = _fetchone(
            connection,
            "SELECT id, name, room, type, is_on, power_kw FROM devices WHERE id = ?",
            (device_id,),
        )

    if row is None:
        return None
    return _device_from_row(row)


def create_device(device: DeviceCreate) -> DeviceResponse:
    ensure_database()
    with connect() as connection:
        device_id = _next_device_id(connection, device.name)
        created = DeviceResponse(id=device_id, **device.model_dump())
        _execute(
            connection,
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
        row = _fetchone(
            connection,
            "SELECT id, name, room, type, is_on, power_kw FROM devices WHERE id = ?",
            (device_id,),
        )
        if row is None:
            return None

        device = _device_from_row(row)
        updated = device.model_copy(update={"is_on": not device.is_on})
        if not updated.is_on:
            updated = updated.model_copy(update={"power_kw": 0.0})
        elif updated.power_kw == 0:
            updated = updated.model_copy(update={"power_kw": _default_power_kw(device)})

        _execute(
            connection,
            "UPDATE devices SET is_on = ?, power_kw = ? WHERE id = ?",
            (int(updated.is_on), updated.power_kw, device_id),
        )
        return updated


def set_device_state(device_id: str, state: bool) -> DeviceResponse | None:
    ensure_database()
    with connect() as connection:
        row = _fetchone(
            connection,
            "SELECT id, name, room, type, is_on, power_kw FROM devices WHERE id = ?",
            (device_id,),
        )
        if row is None:
            return None

        device = _device_from_row(row)
        next_power_kw = device.power_kw
        if not state:
            next_power_kw = 0.0
        elif next_power_kw == 0:
            next_power_kw = _default_power_kw(device)

        _execute(
            connection,
            "UPDATE devices SET is_on = ?, power_kw = ? WHERE id = ?",
            (int(state), next_power_kw, device_id),
        )

    return get_device(device_id)


def get_billing_summary() -> dict[str, float | int | str]:
    ensure_database()
    with connect() as connection:
        row = _fetchone(connection, "SELECT * FROM billing_summary WHERE id = 1")
        if row is None:
            raise ValueError("Billing summary data is not available in the database")

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
        if USE_MYSQL:
            _execute(
                connection,
                """
                INSERT INTO billing_summary (
                    id, current_balance, projected_bill, budget_limit,
                    billing_cycle, solar_credit, days_remaining
                )
                VALUES (1, 0, 0, ?, '', 0, 0)
                ON DUPLICATE KEY UPDATE budget_limit = VALUES(budget_limit)
                """,
                (budget_limit,),
            )
        else:
            _execute(
                connection,
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


def normalize_device_power_defaults() -> None:
    ensure_database()
    with connect() as connection:
        rows = _fetchall(connection, "SELECT id, name, room, type, is_on, power_kw FROM devices")
        for row in rows:
            device = _device_from_row(row)
            if device.is_on and device.power_kw in {0.0, 0.9}:
                _execute(connection, "UPDATE devices SET power_kw = ? WHERE id = ?", (_default_power_kw(device), device.id))


def get_billing_trend() -> list[BillingTrendPoint]:
    ensure_database()
    with connect() as connection:
        rows = _fetchall(
            connection,
            """
            SELECT label, current_bill, projected_bill, savings
            FROM billing_trend
            ORDER BY sort_order
            """,
        )

    return [BillingTrendPoint(**row) for row in rows]


def _next_device_id(connection: Any, name: str) -> str:
    base_id = "".join(char.lower() for char in name if char.isalnum()) or "device"
    device_id = base_id
    index = 2
    while _device_exists(connection, device_id):
        device_id = f"{base_id}-{index}"
        index += 1
    return device_id


def _device_exists(connection: Any, device_id: str) -> bool:
    return _fetchone(connection, "SELECT 1 FROM devices WHERE id = ?", (device_id,)) is not None


def _default_power_kw(device: DeviceResponse) -> float:
    if device.id in DEVICE_POWER_DEFAULTS:
        return DEVICE_POWER_DEFAULTS[device.id]

    normalized = f"{device.name} {device.type}".lower()
    if any(term in normalized for term in ["hvac", "air conditioner", "ac"]):
        return 3.4
    if any(term in normalized for term in ["cooler"]):
        return 1.2
    if any(term in normalized for term in ["fan"]):
        return 0.08
    if any(term in normalized for term in ["charger", "ev"]):
        return 7.2
    if any(term in normalized for term in ["heater", "geyser"]):
        return 4.5
    if any(term in normalized for term in ["light", "lamp", "bulb", "led", "tube light", "tubelight"]):
        return 0.06
    if any(term in normalized for term in ["washer", "washing"]):
        return 0.6
    return 0.8


def _device_from_row(row: dict[str, Any]) -> DeviceResponse:
    values = dict(row)
    values["is_on"] = bool(values["is_on"])
    return DeviceResponse(**values)
