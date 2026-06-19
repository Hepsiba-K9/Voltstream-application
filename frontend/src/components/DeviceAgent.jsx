import {
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
  if (
    error.status === 429 ||
    error.message.includes("Gemini quota is exhausted") ||
    error.message.includes("RESOURCE_EXHAUSTED") ||
    error.message.includes("429")
  ) {
    return "Gemini quota is exhausted right now. Please wait a few minutes, then try again.";
  }
  if (error.message.includes("Backend unavailable")) {
    return "Backend unavailable. Run start_backend.bat from the project folder and keep that window open.";
  }
  if (error.message.includes("non-JSON response")) {
    return "Backend route is misconfigured. Rebuild and redeploy the frontend with the backend API URL.";
  }
  return error.message;
}

function stateLabel(device) {
  if (!device) return "No device selected";
  return device.is_on ? "On" : "Off";
}

function formatDeviceResult(response) {
  return response?.answer ?? "";
}

function cleanAnswerText(value = "") {
  return value
    .replace(/\*\*(.*?)\*\*/g, "$1")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

function parseAnswer(value = "") {
  return cleanAnswerText(value)
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const bulletMatch = line.match(/^[-*]\s+(.+)$/);
      if (bulletMatch) return { type: "bullet", text: cleanAnswerText(bulletMatch[1]) };

      const numberedMatch = line.match(/^\d+[.)]\s+(.+)$/);
      if (numberedMatch) return { type: "bullet", text: cleanAnswerText(numberedMatch[1]) };

      const actionLineMatch = line.match(/^(Optimize|Shift|Schedule|Reduce|Turn|Charge|Run|Use|Set|Start|Target)\b(.+)$/i);
      if (actionLineMatch) return { type: "bullet", text: cleanAnswerText(line) };

      if (line.endsWith(":")) return { type: "heading", text: cleanAnswerText(line.replace(/:$/, "")) };
      return { type: "paragraph", text: cleanAnswerText(line) };
    });
}

function AgentAnswer({ text }) {
  const blocks = parseAnswer(text);
  const rendered = [];
  let bullets = [];

  function flushBullets(key) {
    if (bullets.length === 0) return;
    const current = bullets;
    bullets = [];
    rendered.push(
      <ul className="assistant-answer-list" key={`list-${key}`}>
        {current.map((item, index) => (
          <li key={`${item}-${index}`}>{item}</li>
        ))}
      </ul>
    );
  }

  blocks.forEach((block, index) => {
    if (block.type === "bullet") {
      bullets.push(block.text);
      return;
    }

    flushBullets(index);
    if (block.type === "heading") {
      rendered.push(
        <strong className="assistant-answer-heading" key={index}>
          {block.text}
        </strong>
      );
      return;
    }

    rendered.push(<p key={index}>{block.text}</p>);
  });
  flushBullets("end");

  return <div className="assistant-answer-content">{rendered}</div>;
}

function AgentLoop({ loop = [] }) {
  if (!loop || loop.length === 0) return null;

  return (
    <details className="agent-trace">
      <summary>
        <span>Agent Loop</span>
        <small>{loop.length} steps</small>
      </summary>
      <div className="agent-trace-content">
        <ol className="agent-loop-list">
          {loop.map((step, index) => (
            <li key={`${step}-${index}`}>
              <span>{index + 1}</span>
              <p>{step}</p>
            </li>
          ))}
        </ol>
      </div>
    </details>
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
          agentLoop: response.agent_loop ?? [],
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
                    {message.role === "agent" && !message.isError ? (
                      <AgentAnswer text={message.text} />
                    ) : (
                      <p>{message.text}</p>
                    )}
                    {message.role === "agent" && !message.isError && (
                      <AgentLoop loop={message.agentLoop} />
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
