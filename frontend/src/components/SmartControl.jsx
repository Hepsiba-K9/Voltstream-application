import {
  AirVent,
  BatteryCharging,
  Grid2X2,
  Lightbulb,
  List,
  Plus,
  Power,
  Shirt,
  SlidersHorizontal,
  Thermometer,
  Zap,
} from "lucide-react";
import { useState } from "react";
import { addDevice, getDevices, getUsageHistory, toggleDevice } from "../api";
import { useAsync } from "../hooks";
import { ErrorState, LoadingState } from "../ui/State";

const deviceIcons = {
  Climate: AirVent,
  Mobility: BatteryCharging,
  Appliance: Shirt,
  Thermal: Thermometer,
  Lighting: Lightbulb,
};

const energyPeriods = {
  week: "weekly",
  month: "monthly",
  year: "monthly",
};

export function SmartControl() {
  const { data, error, loading, setData } = useAsync(getDevices, []);
  const [showForm, setShowForm] = useState(false);
  const [typeFilter, setTypeFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");
  const [viewMode, setViewMode] = useState("grid");
  const [formStatus, setFormStatus] = useState("");
  const [saving, setSaving] = useState(false);
  const [selectedDeviceId, setSelectedDeviceId] = useState("");
  const [onTime, setOnTime] = useState("18:00");
  const [offTime, setOffTime] = useState("05:00");
  const [intensity, setIntensity] = useState(68);
  const [energyPeriod, setEnergyPeriod] = useState("week");
  const {
    data: energyData,
    error: energyError,
    loading: energyLoading,
  } = useAsync(() => getUsageHistory(energyPeriods[energyPeriod]), [energyPeriod]);
  const [selectedRoom, setSelectedRoom] = useState("all");
  const [form, setForm] = useState({
    name: "",
    room: "",
    type: "Appliance",
    is_on: true,
    power_kw: 0.8,
  });

  async function handleToggle(id) {
    await toggleDevice(id);
    const devices = await getDevices();
    setData(devices);
  }

  async function handleAddDevice(event) {
    event.preventDefault();
    setSaving(true);
    setFormStatus("");

    try {
      await addDevice({
        ...form,
        power_kw: Number(form.power_kw) || 0,
      });
      const devices = await getDevices();
      setData(devices);
      setShowForm(false);
      setFormStatus("Device added successfully.");
      setForm({
        name: "",
        room: "",
        type: "Appliance",
        is_on: true,
        power_kw: 0.8,
      });
    } catch (err) {
      setFormStatus(err instanceof Error ? err.message : "Could not add device.");
    } finally {
      setSaving(false);
    }
  }

  const filteredDevices = (data ?? []).filter((device) => {
    const matchesType = typeFilter === "all" || device.type === typeFilter;
    const matchesStatus =
      statusFilter === "all" ||
      (statusFilter === "on" && device.is_on) ||
      (statusFilter === "off" && !device.is_on);
    const matchesRoom = selectedRoom === "all" || device.room === selectedRoom;

    return matchesType && matchesStatus && matchesRoom;
  });
  const rooms = [...new Set((data ?? []).map((device) => device.room))];
  const selectedDevice =
    (data ?? []).find((device) => device.id === selectedDeviceId) ?? filteredDevices[0] ?? (data ?? [])[0];
  const devicesOn = (data ?? []).filter((device) => device.is_on).length;
  const activeLoad = (data ?? []).reduce((total, device) => total + (device.is_on ? device.power_kw : 0), 0);
  const focusIcon = selectedDevice ? deviceIcons[selectedDevice.type] ?? Power : Power;
  const FocusIcon = focusIcon;
  const energyBars = (energyData ?? []).map((item) => ({
    label: item.label,
    value: Math.max(0, item.grid_kwh + item.solar_kwh),
  }));
  const maxEnergyValue = Math.max(...energyBars.map((bar) => bar.value), 1);

  return (
    <section className="app-page smart-page">
      <header className="section-header">
        <div>
          <h1>Devices</h1>
          <p>Manage your smart devices.</p>
        </div>
        <button
          className="primary-action"
          onClick={() => {
            setShowForm((value) => !value);
            setFormStatus("");
          }}
          type="button"
        >
          <Plus size={17} />
          <span>Add Device</span>
        </button>
      </header>

      {showForm && (
        <form className="add-device-panel" onSubmit={handleAddDevice}>
          <label>
            Device name
            <input
              required
              value={form.name}
              onChange={(event) => setForm({ ...form, name: event.target.value })}
              placeholder="Air Purifier"
            />
          </label>
          <label>
            Room
            <input
              required
              value={form.room}
              onChange={(event) => setForm({ ...form, room: event.target.value })}
              placeholder="Bedroom"
            />
          </label>
          <label>
            Type
            <select value={form.type} onChange={(event) => setForm({ ...form, type: event.target.value })}>
              <option>Appliance</option>
              <option>Climate</option>
              <option>Lighting</option>
              <option>Mobility</option>
              <option>Thermal</option>
            </select>
          </label>
          <label>
            Power kW
            <input
              min="0"
              step="0.1"
              type="number"
              value={form.power_kw}
              onChange={(event) => setForm({ ...form, power_kw: event.target.value })}
            />
          </label>
          <label className="checkbox-field">
            <input
              checked={form.is_on}
              type="checkbox"
              onChange={(event) => setForm({ ...form, is_on: event.target.checked })}
            />
            Start switched on
          </label>
          <div className="form-actions">
            <button
              type="button"
              onClick={() => {
                setShowForm(false);
                setFormStatus("");
              }}
            >
              Cancel
            </button>
            <button className="primary-action" disabled={saving} type="submit">
              {saving ? "Saving..." : "Save Device"}
            </button>
          </div>
        </form>
      )}
      {formStatus && <p className={`form-status ${formStatus.includes("successfully") ? "success" : "error"}`}>{formStatus}</p>}

      <div className="device-toolbar">
        <label className="filter-control">
          <SlidersHorizontal size={16} />
          <select value={typeFilter} onChange={(event) => setTypeFilter(event.target.value)}>
            <option value="all">All Devices</option>
            <option value="Climate">Climate</option>
            <option value="Appliance">Appliance</option>
            <option value="Lighting">Lighting</option>
            <option value="Mobility">Mobility</option>
            <option value="Thermal">Thermal</option>
          </select>
        </label>
        <label className="filter-control">
          <SlidersHorizontal size={16} />
          <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
            <option value="all">All Status</option>
            <option value="on">ON</option>
            <option value="off">OFF</option>
          </select>
        </label>
        <div className="view-toggle">
          <button
            className={viewMode === "grid" ? "selected" : ""}
            onClick={() => setViewMode("grid")}
            type="button"
            aria-label="Grid view"
          >
            <Grid2X2 size={18} />
          </button>
          <button
            className={viewMode === "list" ? "selected" : ""}
            onClick={() => setViewMode("list")}
            type="button"
            aria-label="List view"
          >
            <List size={18} />
          </button>
        </div>
      </div>

      {loading && <LoadingState />}
      {error && <ErrorState message={error} />}
      {data && (
        <>
          <div className="device-top-metrics">
            <article className="white-info-card dark">
              <span>Current Consumption</span>
              <strong>{activeLoad.toFixed(1)} kW</strong>
            </article>
            <article className="white-info-card">
              <span>Devices On</span>
              <strong>{devicesOn}</strong>
            </article>
            <article className="white-info-card">
              <span>Total Devices</span>
              <strong>{data.length}</strong>
            </article>
          </div>

          <div className="white-smart-console no-thermostat">
            {selectedDevice && (
              <article className="white-featured-panel">
              <div className="white-device-art">
                <FocusIcon size={86} />
              </div>
              <div className="white-featured-copy">
                <span>Device</span>
                <h2>{selectedDevice.name}</h2>
                <p>{selectedDevice.room}</p>
              </div>
              <button
                className={`console-power-button ${selectedDevice.is_on ? "on" : ""}`}
                onClick={() => handleToggle(selectedDevice.id)}
                type="button"
                aria-label={`Turn ${selectedDevice.name} ${selectedDevice.is_on ? "off" : "on"}`}
              >
                <Power size={19} />
              </button>
              <div className="white-featured-stats">
                <div>
                  <strong>{selectedDevice.is_on ? "ON" : "OFF"}</strong>
                  <span>Database Status</span>
                </div>
                <div>
                  <strong>{selectedDevice.power_kw.toFixed(1)} kW</strong>
                  <span>Energy Consumption</span>
                </div>
              </div>
              <div className="white-schedule-row">
                <label>
                  On time
                  <input type="time" value={onTime} onChange={(event) => setOnTime(event.target.value)} />
                </label>
                <label>
                  Off time
                  <input type="time" value={offTime} onChange={(event) => setOffTime(event.target.value)} />
                </label>
              </div>
              <label className="white-intensity">
                <Zap size={16} />
                <input
                  max="100"
                  min="0"
                  type="range"
                  value={intensity}
                  onChange={(event) => setIntensity(event.target.value)}
                />
                <strong>{intensity}%</strong>
              </label>
            </article>
          )}

          <article className="white-energy-panel graph-control-slot">
            <div className="white-panel-head">
              <div>
                <span>Power Consumption</span>
                <h2>{activeLoad.toFixed(1)} kWh</h2>
              </div>
              <div className="energy-periods">
                {["week", "month", "year"].map((periodItem) => (
                  <button
                    className={energyPeriod === periodItem ? "selected" : ""}
                    key={periodItem}
                    onClick={() => setEnergyPeriod(periodItem)}
                    type="button"
                  >
                    {periodItem}
                  </button>
                ))}
              </div>
            </div>
            {energyLoading && <p className="muted-footer">Loading graph data...</p>}
            {energyError && <p className="muted-footer">{energyError}</p>}
            <div className="white-bar-chart">
              {energyBars.map((bar, index) => (
                <div key={bar.label}>
                  <span
                    className={index === 3 ? "highlight" : ""}
                    style={{ height: `${Math.max(8, (bar.value / maxEnergyValue) * 100)}%` }}
                    title={`${bar.label}: ${bar.value.toFixed(1)} kWh`}
                  />
                  <b>{bar.label}</b>
                </div>
              ))}
            </div>
          </article>

          <section className="device-card-strip">
            {filteredDevices.map((device) => (
              <article className={`white-device-tile ${selectedDevice?.id === device.id ? "selected" : ""}`} key={device.id}>
                <button className="tile-select" type="button" onClick={() => setSelectedDeviceId(device.id)}>
                  {(() => {
                    const Icon = deviceIcons[device.type] ?? Power;
                    return <Icon size={22} />;
                  })()}
                  <span>{device.room}</span>
                  <strong>{device.name}</strong>
                </button>
                <button
                  className={`mini-switch ${device.is_on ? "on" : ""}`}
                  onClick={() => handleToggle(device.id)}
                  type="button"
                  aria-label={`Turn ${device.name} ${device.is_on ? "off" : "on"}`}
                  title={`Turn ${device.name} ${device.is_on ? "off" : "on"}`}
                >
                  <span />
                </button>
                <b>{device.is_on ? "ON" : "OFF"} · {device.power_kw.toFixed(1)} kW</b>
              </article>
            ))}
          </section>

          <article className="white-home-panel">
            <div className="home-chip-row">
              <span>{devicesOn} ON</span>
              <span>{activeLoad.toFixed(1)} kW</span>
              <span>{data.length} devices</span>
            </div>
            <div className="white-house-visual">
              <div className="house-sun" />
              <div className="house-roof" />
              <div className="solar-panel-row">
                <span />
                <span />
                <span />
              </div>
              <div className="house-body">
                <span className="house-window" />
                <span className="house-door" />
                <span className="house-window" />
              </div>
              <div className="house-ground" />
            </div>
          </article>

          <nav className="white-room-nav" aria-label="Device rooms">
            <button
              className={selectedRoom === "all" ? "selected" : ""}
              onClick={() => setSelectedRoom("all")}
              type="button"
            >
              All Rooms
            </button>
            {rooms.map((room) => (
              <button
                className={selectedRoom === room ? "selected" : ""}
                key={room}
                onClick={() => setSelectedRoom(room)}
                type="button"
              >
                {room}
              </button>
            ))}
            <button
              className="add-room-button"
              onClick={() => {
                setShowForm(true);
                setFormStatus("");
              }}
              type="button"
              aria-label="Add device"
            >
              <Plus size={18} />
            </button>
          </nav>
        </div>
        </>
      )}
      {data && filteredDevices.length === 0 && <p className="muted-footer">No devices match the selected filters.</p>}
      {data && <p className="muted-footer">{filteredDevices.length} of {data.length} devices</p>}
    </section>
  );
}
