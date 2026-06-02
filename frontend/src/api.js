const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";
const REQUEST_TIMEOUT_MS = 8000;
const AI_TIMEOUT_MS = 90000;

async function request(path, options = {}) {
  const controller = new AbortController();
  const externalSignal = options.signal;
  const timeoutMs = path === "/api/v1/chat" || path === "/api/v1/qa" || path === "/api/v1/agent"
      ? AI_TIMEOUT_MS
      : REQUEST_TIMEOUT_MS;
  const timeoutId = window.setTimeout(() => controller.abort(), timeoutMs);
  if (externalSignal) {
    externalSignal.addEventListener("abort", () => controller.abort(), { once: true });
  }

  let response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      ...options,
      signal: controller.signal,
    });
  } catch (error) {
    throw new Error(error.name === "AbortError" ? "Backend request timed out" : "Backend unavailable");
  } finally {
    window.clearTimeout(timeoutId);
  }

  if (!response.ok) {
    let detail = `Request failed: ${response.status}`;
    try {
      const errorBody = await response.json();
      detail = errorBody.detail ?? detail;
    } catch {
      // Keep the status-only message when the API does not return JSON.
    }
    throw new Error(detail);
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

export function updateBillingLimit(budgetLimit) {
  return request("/api/v1/billing/summary", {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ budget_limit: budgetLimit }),
  });
}

export function getBillingTrend() {
  return request("/api/v1/billing/trend");
}

export function sendChatMessage(message, signal) {
  return request("/api/v1/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
    signal,
  });
}

export function sendAgentMessage(message, signal, agentType = "device") {
  return request("/api/v1/agent", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, agent_type: agentType }),
    signal,
  });
}

export function askDocumentQuestion(question, signal) {
  return request("/api/v1/qa", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
    signal,
  });
}
