from data_models import DeviceResponse, EnergyDataPoint, LivePowerSample, LivePowerStatus


LIVE_STATUS = LivePowerStatus(
    grid_draw_kw=2.5,
    solar_generation_kw=4.8,
    net_usage_kw=-2.3,
    battery_percent=76,
    home_load_kw=2.4,
    updated_at="2026-05-06T10:15:00+05:30",
    live_series=[
        LivePowerSample(label="6 AM", grid_kw=5.0, solar_kw=0.2),
        LivePowerSample(label="9 AM", grid_kw=4.1, solar_kw=3.2),
        LivePowerSample(label="12 PM", grid_kw=2.2, solar_kw=4.9),
        LivePowerSample(label="3 PM", grid_kw=1.5, solar_kw=4.6),
        LivePowerSample(label="6 PM", grid_kw=3.8, solar_kw=2.5),
        LivePowerSample(label="9 PM", grid_kw=5.2, solar_kw=0.1),
    ],
)

HISTORY = {
    "daily": [
        EnergyDataPoint(label="6 AM", grid_kwh=0.8, solar_kwh=0.2, net_kwh=0.6),
        EnergyDataPoint(label="9 AM", grid_kwh=1.1, solar_kwh=2.7, net_kwh=-1.6),
        EnergyDataPoint(label="12 PM", grid_kwh=0.4, solar_kwh=5.1, net_kwh=-4.7),
        EnergyDataPoint(label="3 PM", grid_kwh=0.7, solar_kwh=4.3, net_kwh=-3.6),
        EnergyDataPoint(label="6 PM", grid_kwh=2.8, solar_kwh=0.9, net_kwh=1.9),
        EnergyDataPoint(label="9 PM", grid_kwh=3.2, solar_kwh=0.0, net_kwh=3.2),
    ],
    "weekly": [
        EnergyDataPoint(label="Mon", grid_kwh=16, solar_kwh=28, net_kwh=-12),
        EnergyDataPoint(label="Tue", grid_kwh=18, solar_kwh=25, net_kwh=-7),
        EnergyDataPoint(label="Wed", grid_kwh=14, solar_kwh=31, net_kwh=-17),
        EnergyDataPoint(label="Thu", grid_kwh=19, solar_kwh=23, net_kwh=-4),
        EnergyDataPoint(label="Fri", grid_kwh=22, solar_kwh=20, net_kwh=2),
        EnergyDataPoint(label="Sat", grid_kwh=25, solar_kwh=26, net_kwh=-1),
        EnergyDataPoint(label="Sun", grid_kwh=17, solar_kwh=30, net_kwh=-13),
    ],
    "monthly": [
        EnergyDataPoint(label="Week 1", grid_kwh=120, solar_kwh=188, net_kwh=-68),
        EnergyDataPoint(label="Week 2", grid_kwh=132, solar_kwh=176, net_kwh=-44),
        EnergyDataPoint(label="Week 3", grid_kwh=148, solar_kwh=159, net_kwh=-11),
        EnergyDataPoint(label="Week 4", grid_kwh=141, solar_kwh=193, net_kwh=-52),
    ],
}

DEVICES = {
    "hvac": DeviceResponse(
        id="hvac",
        name="Living Room HVAC",
        room="Living Room",
        type="Climate",
        is_on=True,
        power_kw=1.6,
    ),
    "charger": DeviceResponse(
        id="charger",
        name="EV Charger",
        room="Garage",
        type="Mobility",
        is_on=False,
        power_kw=0.0,
    ),
    "washer": DeviceResponse(
        id="washer",
        name="Smart Washer",
        room="Utility",
        type="Appliance",
        is_on=True,
        power_kw=0.7,
    ),
    "heater": DeviceResponse(
        id="heater",
        name="Water Heater",
        room="Basement",
        type="Thermal",
        is_on=True,
        power_kw=1.2,
    ),
}

BILLING_SUMMARY = {
    "current_balance": 48.62,
    "projected_bill": 152.40,
    "budget_limit": 120.00,
    "billing_cycle": "May 2026",
    "solar_credit": 28.15,
    "days_remaining": 14,
}
