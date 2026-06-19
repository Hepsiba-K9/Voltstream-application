import { Bot, ExternalLink, Send, X } from "lucide-react";
import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { sendChatMessage } from "../api";

function cleanAnswerText(value) {
  return value
    .replace(/\*\*(.*?)\*\*/g, "$1")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

function formatAssistantError(error) {
  if (
    error.message.includes("GOOGLE_GENAI_USE_VERTEXAI") ||
    error.message.includes("GOOGLE_CLOUD_PROJECT") ||
    error.message.includes("GEMINI_API_KEY")
  ) {
    return "Gemini is not configured yet. Add Vertex AI settings to .env and restart the backend.";
  }
  if (error.message.includes("Backend unavailable")) {
    return "Backend unavailable. Start the backend and try again.";
  }
  return error.message;
}

export function FloatingAssistant() {
  const location = useLocation();
  const [input, setInput] = useState("");
  const [answer, setAnswer] = useState("");
  const [question, setQuestion] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isPanelOpen, setIsPanelOpen] = useState(false);

  if (location.pathname.startsWith("/assistant") || location.pathname.startsWith("/agent")) {
    return null;
  }

  async function handleSubmit(event) {
    event.preventDefault();
    const prompt = input.trim();
    if (!prompt || isLoading) return;

    setInput("");
    setQuestion(prompt);
    setAnswer("");
    setIsPanelOpen(true);
    setIsLoading(true);

    try {
      const response = await sendChatMessage(prompt);
      setAnswer(cleanAnswerText(response.answer));
    } catch (error) {
      setAnswer(formatAssistantError(error));
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <aside className="floating-assistant" aria-label="VoltSenseBot quick assistant">
      {isPanelOpen && (
        <section className="floating-assistant-panel">
          <div className="floating-assistant-head">
            <span>
              <Bot size={16} />
              VoltSenseBot
            </span>
            <button type="button" onClick={() => setIsPanelOpen(false)} aria-label="Close assistant answer">
              <X size={16} />
            </button>
          </div>
          {question && <p className="floating-assistant-question">{question}</p>}
          <div className="floating-assistant-answer">
            {isLoading ? "Thinking..." : answer}
          </div>
          <Link to="/assistant/chat" className="floating-assistant-link">
            <ExternalLink size={15} />
            Open full chat
          </Link>
        </section>
      )}

      <form className="floating-assistant-form" onSubmit={handleSubmit}>
        <Bot size={18} />
        <input
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder="Ask VoltSenseBot..."
          aria-label="Ask VoltSenseBot"
        />
        <button type="submit" disabled={isLoading || !input.trim()} aria-label="Send quick question">
          <Send size={17} />
        </button>
      </form>
    </aside>
  );
}
