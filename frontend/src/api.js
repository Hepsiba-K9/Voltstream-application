const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";

async function request(path, options) {
  const response = await fetch(`${API_BASE}${path}`, options);
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json();
}

export function getLiveStatus() {
  return request("/api/v1/dashboard/live");
}

export function getUsageHistory(period) {
  return request(`/api/v1/analytics/history?period=${period}`);
}

export function getDevices() {
  return request("/api/v1/devices");
}

export function addDevice(device) {
  return request("/api/v1/devices", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(device),
  });
}

export function toggleDevice(deviceId) {
  return request(`/api/v1/devices/${deviceId}`, { method: "PATCH" });
}

export function getBillingSummary() {
  return request("/api/v1/billing/summary");
}
