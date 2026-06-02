import {
  Activity,
  ArrowRight,
  Cpu,
  LineChart,
  Send,
} from "lucide-react";
import { useRef, useState } from "react";
import { sendAgentMessage } from "../api";
import voltAgentRobot from "../assets/volt-agent-robot.png";

const agentModes = [
  { id: "device", label: "Device Agent", icon: Cpu },
  { id: "energy", label: "Energy Usage", icon: LineChart },
];

const modeContent = {
  device: {
    name: "Device Agent",
    empty: "Control devices with",
    loading: "Checking device status...",
    placeholder: "Try: Turn off the Air Conditioning",
  },
  energy: {
    name: "Energy Usage Agent",
    empty: "Review energy usage with",
    loading: "Analyzing energy usage...",
    placeholder: "Try: Show last week's usage and savings tips",
  },
};

function formatAgentError(error) {
  if (error.message.includes("Backend unavailable")) {
    return "Backend unavailable. Run start_backend.bat from the project folder and keep that window open.";
  }
  return error.message;
}

function stateLabel(device) {
  if (!device) return "No device selected";
  return device.is_on ? "On" : "Off";
}

function formatDeviceResult(response) {
  if (!response?.device) return response?.answer ?? "";

  const state = response.device.is_on ? "on" : "off";
  const addedDevice = response.tool_calls?.some((call) => call.tool === "add_device");
  const changedState = response.tool_calls?.some((call) => call.tool === "toggle_device");
  const summary = addedDevice
    ? `${response.device.name} added successfully.`
    : changedState
    ? `${response.device.name} turned ${state} successfully.`
    : `${response.device.name} is currently ${state}.`;

  return [
    summary,
    "",
    "Device Status",
    `Name: ${response.device.name}`,
    `Room: ${response.device.room}`,
    `State: ${stateLabel(response.device)}`,
    `Power: ${response.device.power_kw} kW`,
  ].join("\n");
}

function formatTraceValue(value) {
  if (value === null || value === undefined) return "";
  if (typeof value === "boolean") return value ? "true" : "false";
  if (typeof value === "number") return Number.isInteger(value) ? String(value) : value.toFixed(1);
  return String(value).replace(/^voltstream_/, "").replaceAll("_", " ");
}

function describeTraceCall(call) {
  const task = call.args?.task ? formatTraceValue(call.args.task) : "";
  const route = call.result?.route ? formatTraceValue(call.result.route) : "";
  const agent = call.result?.agent ? formatTraceValue(call.result.agent) : call.tool;
  const metrics = [];

  if (call.result?.total_grid_kwh !== undefined) metrics.push(`grid ${formatTraceValue(call.result.total_grid_kwh)} kWh`);
  if (call.result?.total_net_kwh !== undefined) metrics.push(`net ${formatTraceValue(call.result.total_net_kwh)} kWh`);
  if (call.result?.highest_day) metrics.push(`peak ${formatTraceValue(call.result.highest_day)}`);
  if (call.result?.highest_point) metrics.push(`peak ${formatTraceValue(call.result.highest_point)}`);
  if (call.result?.period) metrics.push(`period ${formatTraceValue(call.result.period)}`);
  if (call.result?.recommendation_count !== undefined) metrics.push(`${formatTraceValue(call.result.recommendation_count)} recommendations`);
  if (call.result?.target_savings_kwh !== undefined) metrics.push(`target ${formatTraceValue(call.result.target_savings_kwh)} kWh`);

  if (route) return `${agent} routed ${task || "request"} to ${route}`;
  if (task && metrics.length) return `${agent} completed ${task}: ${metrics.join(", ")}`;
  if (task) return `${agent} completed ${task}`;
  return agent;
}

function AgentTrace({ loop = [], calls = [] }) {
  if (!loop.length && !calls.length) return null;

  return (
    <div className="agent-trace" aria-label="Agent trace log">
      <div className="agent-trace-title">
        <Activity size={16} />
        <span>Trace Log</span>
      </div>
      {loop.length > 0 && (
        <ol className="agent-loop-list">
          {loop.map((step, index) => (
            <li key={`${step}-${index}`}>
              <span>{index + 1}</span>
              <p>{step}</p>
            </li>
          ))}
        </ol>
      )}
      {calls.length > 0 && (
        <div className="agent-tool-trace">
          {calls.map((call, index) => (
            <div className="agent-tool-step" key={`${call.tool}-${index}`}>
              <ArrowRight size={14} />
              <p>{describeTraceCall(call)}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export function DeviceAgent() {
  const [mode, setMode] = useState("device");
  const [input, setInput] = useState("");
  const [messagesByMode, setMessagesByMode] = useState({ device: [], energy: [] });
  const [isLoading, setIsLoading] = useState(false);
  const requestControllerRef = useRef(null);
  const activeContent = modeContent[mode];
  const ActiveIcon = agentModes.find((item) => item.id === mode)?.icon ?? Cpu;
  const messages = messagesByMode[mode];

  function updateMessages(nextMode, updater) {
    setMessagesByMode((current) => ({
      ...current,
      [nextMode]: updater(current[nextMode]),
    }));
  }

  async function submitPrompt(prompt) {
    const message = prompt.trim();
    if (!message || isLoading) return;

    setInput("");
    setIsLoading(true);
    const requestController = new AbortController();
    requestControllerRef.current = requestController;
    const requestMode = mode;
    updateMessages(requestMode, (current) => [...current, { role: "user", text: message }]);

    try {
      const response = await sendAgentMessage(message, requestController.signal, requestMode);
      updateMessages(requestMode, (current) => [
        ...current,
        {
          role: "agent",
          text: requestMode === "device" ? formatDeviceResult(response) : response.answer,
          trace: response.tool_calls ?? [],
          loop: response.agent_loop ?? [],
        },
      ]);
    } catch (error) {
      updateMessages(requestMode, (current) => [
        ...current,
        {
          role: "agent",
          text: requestController.signal.aborted ? "Request stopped." : formatAgentError(error),
          isError: true,
        },
      ]);
    } finally {
      setIsLoading(false);
      requestControllerRef.current = null;
    }
  }

  function handleSubmit(event) {
    event.preventDefault();
    submitPrompt(input);
  }

  function stopRequest() {
    requestControllerRef.current?.abort();
  }

  function handleModeSelect(nextMode) {
    if (nextMode === mode || isLoading) return;
    setMode(nextMode);
    setInput("");
  }

  return (
    <section className="assistant-page agent-chat-page">
      <header className="assistant-header">
        <div>
          <p className="eyebrow">Volt Agent</p>
          <div className="assistant-title-row">
            <h1>Volt Agent</h1>
            <span className="assistant-online">
              <i />
              Online
            </span>
          </div>
        </div>
        <div className="assistant-badge agent-badge">
          <ActiveIcon size={22} />
          <span>{activeContent.name}</span>
          <i />
        </div>
      </header>

      <div className="assistant-workspace">
        <div className="assistant-main-panel">
          <div className="assistant-toolbar">
            <div className="assistant-mode-switch" role="tablist" aria-label="Volt agent mode">
              {agentModes.map(({ id, label, icon: Icon }) => (
                <button
                  key={id}
                  type="button"
                  className={mode === id ? "selected" : ""}
                  onClick={() => handleModeSelect(id)}
                  disabled={isLoading}
                >
                  <Icon size={18} />
                  <span>{label}</span>
                </button>
              ))}
            </div>
          </div>

          <div className="assistant-console agent-chat-console">
            <div className="assistant-thread">
              {messages.length === 0 ? (
                <div className="assistant-empty assistant-welcome agent-welcome">
                  <img
                    className="agent-robot-image"
                    src={voltAgentRobot}
                    alt="Volt Agent"
                  />
                  <div className="assistant-welcome-copy">
                    <h2>
                      {activeContent.empty} <span>{activeContent.name}</span>
                    </h2>
                  </div>
                </div>
              ) : (
                messages.map((message, index) => (
                  <article
                    className={`assistant-message ${message.role === "user" ? "user" : "assistant"} ${
                      message.isError ? "error" : ""
                    }`}
                    key={`${message.role}-${index}`}
                  >
                    <div className="assistant-message-head">
                      <span>{message.role === "user" ? "You" : activeContent.name}</span>
                    </div>
                    <p>{message.text}</p>
                    {message.role === "agent" && (
                      <AgentTrace loop={message.loop} calls={message.trace} />
                    )}
                  </article>
                ))
              )}

              {isLoading && (
                <article className="assistant-message assistant">
                  <div className="assistant-message-head">
                    <span>{activeContent.name}</span>
                    <button type="button" onClick={stopRequest}>
                      Stop
                    </button>
                  </div>
                  <p>{activeContent.loading}</p>
                </article>
              )}
            </div>

            <form className="assistant-form" onSubmit={handleSubmit}>
              <input
                value={input}
                onChange={(event) => setInput(event.target.value)}
                placeholder={activeContent.placeholder}
              />
              <button type="submit" disabled={isLoading || !input.trim()} aria-label="Send">
                <Send size={18} />
              </button>
            </form>
          </div>
        </div>
      </div>
    </section>
  );
}
