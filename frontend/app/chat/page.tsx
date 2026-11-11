"use client";
import { useEffect, useRef, useState } from "react";
import type { ChatMessage, Citation } from "@/lib/api";
import { sendChatMessage, submitFeedback } from "@/lib/api";
import { loadProfile, randomSessionId } from "@/lib/utils";

interface Message {
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
  is_refusal?: boolean;
}

const SESSION_ID_KEY = "placement_copilot_session";

function getSessionId(): string {
  if (typeof window === "undefined") return "ssr";
  let id = sessionStorage.getItem(SESSION_ID_KEY);
  if (!id) {
    id = randomSessionId();
    sessionStorage.setItem(SESSION_ID_KEY, id);
  }
  return id;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSend(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim() || loading) return;
    const userMsg: Message = { role: "user", content: input.trim() };
    const updatedMessages = [...messages, userMsg];
    setMessages(updatedMessages);
    setInput("");
    setLoading(true);
    setError(null);

    try {
      const profile = loadProfile();
      const apiMessages: ChatMessage[] = updatedMessages.map((m) => ({
        role: m.role,
        content: m.content,
      }));
      const resp = await sendChatMessage(apiMessages, profile, getSessionId());
      setMessages([
        ...updatedMessages,
        {
          role: "assistant",
          content: resp.answer,
          citations: resp.citations,
          is_refusal: resp.is_refusal,
        },
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed");
    } finally {
      setLoading(false);
    }
  }

  async function handleFeedback(index: number, fb: "up" | "down") {
    try {
      await submitFeedback(getSessionId(), index, fb);
    } catch {
      // Feedback is best-effort
    }
  }

  return (
    <div className="flex flex-col" style={{ height: "calc(100vh - 160px)" }}>
      <h1 className="mb-3 text-xl font-bold">Chat</h1>
      <div className="mb-2 rounded bg-blue-50 px-3 py-2 text-xs text-blue-700">
        Answers are based on synthetic placement notices only. Set your profile
        for eligibility checks.
      </div>

      <div className="flex-1 overflow-y-auto rounded border border-gray-200 bg-white p-4 space-y-4">
        {messages.length === 0 && (
          <p className="text-sm text-gray-400">
            Ask something like &quot;What is the minimum CGPA for Nexora
            Systems?&quot; or &quot;What drives are closing this week?&quot;
          </p>
        )}
        {messages.map((msg, i) => (
          <div key={i} className={msg.role === "user" ? "text-right" : "text-left"}>
            <div
              className={`inline-block max-w-[85%] rounded-lg px-3 py-2 text-sm ${
                msg.role === "user"
                  ? "bg-blue-600 text-white"
                  : msg.is_refusal
                  ? "border border-orange-200 bg-orange-50 text-orange-900"
                  : "border border-gray-200 bg-gray-50 text-gray-900"
              }`}
            >
              {msg.content}
            </div>
            {msg.citations && msg.citations.length > 0 && (
              <div className="mt-1 space-y-1">
                {msg.citations.map((c, j) => (
                  <details key={j} className="text-left">
                    <summary className="cursor-pointer text-xs text-blue-600 hover:underline">
                      Source: {c.notice_id}
                    </summary>
                    <p className="mt-1 rounded border border-blue-100 bg-blue-50 px-2 py-1 text-xs text-gray-700">
                      {c.chunk_text}
                    </p>
                  </details>
                ))}
              </div>
            )}
            {msg.role === "assistant" && (
              <div className="mt-1 flex gap-2">
                <button
                  onClick={() => handleFeedback(i, "up")}
                  className="text-xs text-gray-400 hover:text-green-600"
                  aria-label="Helpful"
                >
                  👍
                </button>
                <button
                  onClick={() => handleFeedback(i, "down")}
                  className="text-xs text-gray-400 hover:text-red-600"
                  aria-label="Not helpful"
                >
                  👎
                </button>
              </div>
            )}
          </div>
        ))}
        {loading && (
          <div className="text-sm text-gray-400 italic">Thinking...</div>
        )}
        {error && (
          <div className="rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
            Error: {error}
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <form onSubmit={handleSend} className="mt-3 flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about a placement drive..."
          className="flex-1 rounded border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
          disabled={loading}
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
        >
          Send
        </button>
      </form>
    </div>
  );
}
