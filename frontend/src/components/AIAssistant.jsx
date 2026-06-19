import {
  ArrowRight,
  Bot,
  FileSearch,
  Home,
  LineChart,
  ReceiptText,
  Send,
  Sparkles,
  TabletSmartphone,
} from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { askDocumentQuestion, sendChatMessage } from "../api";

const modes = [
  { id: "chat", label: "Chat", icon: Sparkles },
  { id: "qa", label: "PDF Q&A", icon: FileSearch },
];

const promptCards = [
  {
    title: "Home Energy Tips",
    prompt: "How can I reduce grid usage at home?",
    icon: Home,
    tone: "violet",
  },
  {
    title: "Usage Analysis",
    prompt: "Show me my energy usage summary.",
    icon: LineChart,
    tone: "green",
  },
  {
    title: "Billing Help",
    prompt: "Why is my electricity bill high?",
    icon: ReceiptText,
    tone: "orange",
  },
  {
    title: "Device Insights",
    prompt: "Which device consumes the most energy?",
    icon: TabletSmartphone,
    tone: "blue",
  },
];

function formatAssistantError(error) {
  if (
    error.message.includes("GOOGLE_GENAI_USE_VERTEXAI") ||
    error.message.includes("GOOGLE_CLOUD_PROJECT") ||
    error.message.includes("GEMINI_API_KEY")
  ) {
    return "Gemini is not configured yet. Add Vertex AI settings to .env, then restart the backend.";
  }
  if (error.message.includes("Backend unavailable")) {
    return "Backend unavailable. Run start_backend.bat from the project folder and keep that window open.";
  }
  return error.message;
}

function createSession(mode = "chat", title = "New chat") {
  return {
    id: String(Date.now()),
    title,
    mode,
    messages: [],
    createdAt: new Date().toISOString(),
  };
}

function truncateTitle(value) {
  return value.length > 34 ? `${value.slice(0, 31)}...` : value;
}

function cleanAnswerText(value) {
  return value
    .replace(/\*\*(.*?)\*\*/g, "$1")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

function parseAnswer(value) {
  return cleanAnswerText(value)
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const bulletMatch = line.match(/^[-*]\s+(.+)$/);
      if (bulletMatch) return { type: "bullet", text: cleanAnswerText(bulletMatch[1]) };
      const numberedMatch = line.match(/^\d+[.)]\s+(.+)$/);
      if (numberedMatch) return { type: "bullet", text: cleanAnswerText(numberedMatch[1]) };
      if (line.endsWith(":")) return { type: "heading", text: cleanAnswerText(line.replace(/:$/, "")) };
      return { type: "paragraph", text: cleanAnswerText(line) };
    });
}

function buildSuggestions(message, previousPrompt = "") {
  const text = `${previousPrompt} ${message.text}`.toLowerCase();
  if (message.mode === "qa") {
    if (text.includes("recommend") || text.includes("action")) {
      return ["Show only the recommended actions", "Explain the first action", "Summarize this in 3 bullets"];
    }
    if (text.includes("summary") || text.includes("summarize")) {
      return ["List the key points", "What is most important?", "What should I ask next?"];
    }
    return ["Where is this mentioned?", "Summarize this answer", "What else does the document say?"];
  }
  if (text.includes("grid") || text.includes("solar")) {
    return ["Make a daily usage plan", "What should run during solar hours?", "How do I reduce night grid use?"];
  }
  if (text.includes("battery")) {
    return ["How should I schedule charging?", "What battery habits help lifespan?", "Explain this simply"];
  }
  return ["Make this more practical", "Give me 3 quick steps", "Explain with an example"];
}

function AnswerContent({ text }) {
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
      rendered.push(<strong className="assistant-answer-heading" key={index}>{block.text}</strong>);
    } else {
      rendered.push(<p key={index}>{block.text}</p>);
    }
  });
  flushBullets("end");

  return <div className="assistant-answer-content">{rendered}</div>;
}

export function AIAssistant({ routeMode = "chat" }) {
  const initialMode = routeMode === "qa" ? "qa" : "chat";
  const navigate = useNavigate();
  const [sessions, setSessions] = useState(() => [createSession(initialMode)]);
  const [activeSessionId, setActiveSessionId] = useState(() => sessions[0].id);
  const activeSession = useMemo(
    () => sessions.find((session) => session.id === activeSessionId) ?? sessions[0],
    [activeSessionId, sessions]
  );
  const [mode, setMode] = useState(initialMode);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [editingMessage, setEditingMessage] = useState(null);
  const requestControllerRef = useRef(null);
  const activeMode = modes.find((item) => item.id === mode) ?? modes[0];
  const EmptyIcon = activeMode.icon;
  const messages = activeSession?.messages ?? [];

  useEffect(() => {
    const nextMode = routeMode === "qa" ? "qa" : "chat";
    if (mode === nextMode) return;

    const sessionTitle = nextMode === "qa" ? "PDF Q&A" : "New chat";
    const session = createSession(nextMode, sessionTitle);
    setSessions([session]);
    setActiveSessionId(session.id);
    setMode(nextMode);
    setInput("");
    setEditingMessage(null);
  }, [mode, routeMode]);

  function updateActiveSession(updater) {
    setSessions((current) =>
      current.map((session) =>
        session.id === activeSessionId ? updater(session) : session
      )
    );
  }

  function handleModeSelect(nextMode) {
    setEditingMessage(null);
    const sessionTitle = nextMode === "qa" ? "PDF Q&A" : "New chat";
    const session = createSession(nextMode, sessionTitle);
    setSessions([session]);
    setActiveSessionId(session.id);
    setMode(nextMode);
    setInput("");
    navigate(nextMode === "chat" ? "/assistant/chat" : "/assistant/qa");
  }

  async function handleSubmit(event) {
    event.preventDefault();
    const prompt = input.trim();
    if (!prompt || isLoading) return;

    setInput("");
    setIsLoading(true);
    const requestController = new AbortController();
    requestControllerRef.current = requestController;
    updateActiveSession((session) => ({
      ...session,
      mode,
      title: session.messages.length === 0 ? truncateTitle(prompt) : session.title,
      messages: [...session.messages, { role: "user", mode, text: prompt }],
    }));

    try {
      const response =
        mode === "chat"
          ? await sendChatMessage(prompt, requestController.signal)
          : await askDocumentQuestion(prompt, requestController.signal);
      updateActiveSession((session) => ({
        ...session,
        messages: [
          ...session.messages,
          {
            role: "assistant",
            mode,
            text: cleanAnswerText(response.answer),
            sources: response.sources ?? [],
          },
        ],
      }));
    } catch (error) {
      if (requestController.signal.aborted) {
        updateActiveSession((session) => ({
          ...session,
          messages: [
            ...session.messages,
            {
              role: "assistant",
              mode,
              text: "Generation stopped.",
              isError: true,
            },
          ],
        }));
        return;
      }
      updateActiveSession((session) => ({
        ...session,
        messages: [
          ...session.messages,
          {
            role: "assistant",
            mode,
            text: formatAssistantError(error),
            isError: true,
          },
        ],
      }));
    } finally {
      setIsLoading(false);
      requestControllerRef.current = null;
    }
  }

  async function regenerateFromEdit(index, nextPrompt) {
    const prompt = nextPrompt.trim();
    if (!prompt || isLoading) return;

    const editedMode = messages[index]?.mode ?? mode;
    setEditingMessage(null);
    setIsLoading(true);
    const requestController = new AbortController();
    requestControllerRef.current = requestController;

    updateActiveSession((session) => {
      const keptMessages = session.messages.slice(0, index);
      return {
        ...session,
        mode: editedMode,
        title: index === 0 ? truncateTitle(prompt) : session.title,
        messages: [...keptMessages, { role: "user", mode: editedMode, text: prompt }],
      };
    });

    try {
      const response =
        editedMode === "chat"
          ? await sendChatMessage(prompt, requestController.signal)
          : await askDocumentQuestion(prompt, requestController.signal);
      updateActiveSession((session) => ({
        ...session,
        messages: [
          ...session.messages,
          {
            role: "assistant",
            mode: editedMode,
            text: cleanAnswerText(response.answer),
            sources: response.sources ?? [],
          },
        ],
      }));
    } catch (error) {
      updateActiveSession((session) => ({
        ...session,
        messages: [
          ...session.messages,
          {
            role: "assistant",
            mode: editedMode,
            text: requestController.signal.aborted ? "Generation stopped." : formatAssistantError(error),
            isError: true,
          },
        ],
      }));
    } finally {
      setIsLoading(false);
      requestControllerRef.current = null;
    }
  }

  function stopGeneration() {
    requestControllerRef.current?.abort();
  }

  function editMessage(index) {
    const message = messages[index];
    if (!message || message.role !== "user" || isLoading) return;
    setEditingMessage({ index, text: message.text });
  }

  function submitSuggestion(suggestion) {
    setInput(suggestion);
  }

  function submitPromptCard(prompt) {
    setInput(prompt);
  }

  function handleInputKeyDown(event) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      event.currentTarget.form?.requestSubmit();
    }
  }

  return (
    <section className="assistant-page">
      <header className="assistant-header">
        <div>
          <p className="eyebrow">VoltSenseBot</p>
          <div className="assistant-title-row">
            <h1>VoltSenseBot</h1>
            <span className="assistant-online">
              <i />
              Online
            </span>
          </div>
        </div>
        <div className="assistant-badge">
          <Bot size={22} />
          <span>VoltSenseBot</span>
          <i />
        </div>
      </header>

      <div className="assistant-workspace">
        <div className="assistant-main-panel">
          <div className="assistant-toolbar">
            <div className="assistant-mode-switch" role="tablist" aria-label="Assistant mode">
              {modes.map(({ id, label, icon: Icon }) => (
                <button
                  key={id}
                  type="button"
                  className={mode === id ? "selected" : ""}
                  onClick={() => handleModeSelect(id)}
                >
                  <Icon size={18} />
                  <span>{label}</span>
                </button>
              ))}
            </div>

          </div>

          <div className="assistant-console">
            <div className="assistant-thread">
              {messages.length === 0 ? (
                <div className="assistant-empty assistant-welcome">
                  <div className="assistant-welcome-mark">
                    <EmptyIcon size={42} />
                    <Sparkles size={18} className="assistant-welcome-sparkle" />
                  </div>
                  <div className="assistant-welcome-copy">
                    <h2>
                      Hello! I'm <span>VoltSenseBot</span>
                    </h2>
                    <p>
                      {mode === "chat"
                        ? "Your smart energy assistant. Ask me anything about energy usage, saving tips, devices, billing and more."
                        : "Ask questions from the indexed energy reference documents."}
                    </p>
                  </div>
                  {mode === "chat" && (
                    <div className="assistant-prompt-grid">
                      {promptCards.map(({ title, prompt, icon: Icon, tone }) => (
                        <button
                          key={title}
                          type="button"
                          className={`assistant-prompt-card ${tone}`}
                          onClick={() => submitPromptCard(prompt)}
                        >
                          <span className="assistant-prompt-icon">
                            <Icon size={22} />
                          </span>
                          <strong>{title}</strong>
                          <small>{prompt}</small>
                          <b aria-hidden="true">
                            <ArrowRight size={20} />
                          </b>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              ) : (
                messages.map((message, index) => {
                  const previousPrompt = [...messages]
                    .slice(0, index)
                    .reverse()
                    .find((item) => item.role === "user")?.text ?? "";

                  return (
                  <article
                    key={`${message.role}-${index}`}
                    className={`assistant-message ${message.role} ${message.isError ? "error" : ""}`}
                  >
                    <div className="assistant-message-head">
                      <span>{message.role === "user" ? "You" : message.mode === "qa" ? "PDF Q&A" : "VoltSenseBot"}</span>
                      {message.role === "user" && (
                        <button type="button" onClick={() => editMessage(index)}>
                          Edit
                        </button>
                      )}
                    </div>
                    {editingMessage?.index === index ? (
                      <form
                        className="assistant-edit-form"
                        onSubmit={(event) => {
                          event.preventDefault();
                          regenerateFromEdit(index, editingMessage.text);
                        }}
                      >
                        <input
                          value={editingMessage.text}
                          onChange={(event) => setEditingMessage({ index, text: event.target.value })}
                          autoFocus
                        />
                        <div>
                          <button type="button" onClick={() => setEditingMessage(null)}>
                            Cancel
                          </button>
                          <button type="submit" disabled={!editingMessage.text.trim()}>
                            Save
                          </button>
                        </div>
                      </form>
                    ) : message.role === "assistant" ? (
                      <AnswerContent text={message.text} />
                    ) : (
                      <p>{message.text}</p>
                    )}
                    {message.role === "assistant" && !message.isError && (
                      <div className="assistant-suggestions">
                        {buildSuggestions(message, previousPrompt).map((suggestion) => (
                          <button
                            key={suggestion}
                            type="button"
                            onClick={() => submitSuggestion(suggestion)}
                          >
                            {suggestion}
                          </button>
                        ))}
                      </div>
                    )}
                  </article>
                );
                })
              )}
              {isLoading && (
                <article className="assistant-message assistant">
                  <div className="assistant-message-head">
                    <span>{mode === "qa" ? "PDF Q&A" : "VoltSenseBot"}</span>
                    <button type="button" onClick={stopGeneration}>
                      Stop
                    </button>
                  </div>
                  <p>Thinking...</p>
                </article>
              )}
            </div>

            <form className="assistant-form" onSubmit={handleSubmit}>
              <input
                value={input}
                onChange={(event) => setInput(event.target.value)}
                onKeyDown={handleInputKeyDown}
                placeholder={mode === "chat" ? "Ask an energy-saving question" : "Ask a question from the reference document"}
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
