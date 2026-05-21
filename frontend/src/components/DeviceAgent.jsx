import {
  Cpu,
  Send,
} from "lucide-react";
import { useRef, useState } from "react";
import { sendAgentMessage } from "../api";
import voltAgentRobot from "../assets/volt-agent-robot.png";

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

export function DeviceAgent() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const requestControllerRef = useRef(null);

  async function submitPrompt(prompt) {
    const message = prompt.trim();
    if (!message || isLoading) return;

    setInput("");
    setIsLoading(true);
    const requestController = new AbortController();
    requestControllerRef.current = requestController;
    setMessages((current) => [...current, { role: "user", text: message }]);

    try {
      const response = await sendAgentMessage(message, requestController.signal);
      setMessages((current) => [...current, { role: "agent", text: formatDeviceResult(response) }]);
    } catch (error) {
      setMessages((current) => [
        ...current,
        { role: "agent", text: formatAgentError(error), isError: true },
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
          <Cpu size={22} />
          <span>Volt Agent</span>
          <i />
        </div>
      </header>

      <div className="assistant-workspace">
        <div className="assistant-main-panel">
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
                      Control devices with <span>Volt Agent</span>
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
                      <span>{message.role === "user" ? "You" : "Volt Agent"}</span>
                    </div>
                    <p>{message.text}</p>
                  </article>
                ))
              )}

              {isLoading && (
                <article className="assistant-message assistant">
                  <div className="assistant-message-head">
                    <span>Volt Agent</span>
                    <button type="button" onClick={stopRequest}>
                      Stop
                    </button>
                  </div>
                  <p>Checking device status...</p>
                </article>
              )}
            </div>

            <form className="assistant-form" onSubmit={handleSubmit}>
              <input
                value={input}
                onChange={(event) => setInput(event.target.value)}
                placeholder="Try: Turn off the Air Conditioning"
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
