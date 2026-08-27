import { useState, useRef, useEffect } from "react";
import { Send, Sparkles, Bot, ArrowUpRight } from "lucide-react";

function AIChat() {
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const textareaRef = useRef(null);

  // auto-grow the textarea up to 4 lines, then scroll
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 112) + "px";
  }, [message]);

  const sendMessage = async () => {
    const text = message.trim();
    if (!text || loading) return;

    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setMessage("");
    setError("");
    setLoading(true);

    try {
      const response = await fetch("http://127.0.0.1:8000/ai/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        body: JSON.stringify({ message: text }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data?.detail || "AI request failed");
      }

      const aiReply =
        data?.reply ||
        data?.response ||
        data?.message ||
        data?.answer ||
        JSON.stringify(data);

      setMessages((prev) => [...prev, { role: "assistant", content: aiReply }]);
    } catch (err) {
      setError(err.message || "Unable to connect to AI Assistant");
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  };

  const quickQuestions = [
    "What are my total sales?",
    "How much money is receivable?",
    "How much do we owe suppliers?",
    "What is the net profit?",
    "What is the current stock?",
  ];

  const askQuickQuestion = (question) => {
    setMessage(question);
    textareaRef.current?.focus();
  };

  return (
    <div className="mx-auto max-w-5xl p-6">
      {/* HEADER */}
      <div className="mb-6 flex items-start justify-between">
        <div className="flex items-center gap-4">
          <div
            className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl shadow-sm"
            style={{ background: "linear-gradient(135deg, #4f46e5, #7c3aed)" }}
          >
            <Sparkles size={22} color="white" strokeWidth={2.25} />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-gray-900">
              AI Factory Assistant
            </h1>
            <p className="mt-0.5 text-sm text-gray-500">
              Ask about sales, purchases, stock, profit, receivables, payables
              and factory performance.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 rounded-full border border-green-200 bg-green-50 px-3 py-1.5">
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-green-400 opacity-75" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-green-500" />
          </span>
          <span className="text-xs font-medium text-green-700">Online</span>
        </div>
      </div>

      {/* QUICK QUESTIONS */}
      <div className="mb-4">
        <h2 className="mb-2.5 text-xs font-semibold uppercase tracking-wide text-gray-400">
          Quick questions
        </h2>
        <div className="flex flex-wrap gap-2">
          {quickQuestions.map((question) => (
            <button
              key={question}
              onClick={() => askQuickQuestion(question)}
              className="group inline-flex items-center gap-1.5 rounded-full border border-gray-200 bg-white px-3.5 py-1.5 text-sm text-gray-600 shadow-sm transition-all hover:border-indigo-200 hover:bg-indigo-50 hover:text-indigo-700"
            >
              {question}
              <ArrowUpRight
                size={13}
                className="text-gray-300 transition-colors group-hover:text-indigo-400"
              />
            </button>
          ))}
        </div>
      </div>

      {/* CHAT PANEL */}
      <div className="flex h-[560px] flex-col overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-sm">
        {/* MESSAGES */}
        <div className="flex-1 space-y-4 overflow-y-auto px-6 py-6">
          {messages.length === 0 && (
            <div className="flex h-full items-center justify-center text-center">
              <div className="max-w-sm">
                <div
                  className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl"
                  style={{ background: "linear-gradient(135deg, #4f46e5, #7c3aed)" }}
                >
                  <Bot size={26} color="white" strokeWidth={2} />
                </div>
                <h2 className="text-base font-semibold text-gray-900">
                  How can I help today?
                </h2>
                <p className="mt-1.5 text-sm leading-relaxed text-gray-500">
                  Ask me anything about your rice factory — sales, purchases,
                  stock, payments, profit, or overall performance.
                </p>
              </div>
            </div>
          )}

          {messages.map((item, index) => (
            <div
              key={index}
              className={`flex ${item.role === "user" ? "justify-end" : "justify-start"}`}
            >
              {item.role === "assistant" && (
                <div className="mr-2 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-indigo-100">
                  <Bot size={14} className="text-indigo-600" />
                </div>
              )}
              <div
                className={`max-w-[75%] px-4 py-2.5 text-sm leading-relaxed shadow-sm ${
                  item.role === "user"
                    ? "rounded-2xl rounded-br-sm bg-indigo-600 text-white"
                    : "rounded-2xl rounded-bl-sm bg-gray-100 text-gray-800"
                }`}
              >
                <p className="whitespace-pre-wrap">{item.content}</p>
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex justify-start">
              <div className="mr-2 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-indigo-100">
                <Bot size={14} className="text-indigo-600" />
              </div>
              <div className="flex items-center gap-1.5 rounded-2xl rounded-bl-sm bg-gray-100 px-4 py-3">
                <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-gray-400" />
                <span
                  className="h-1.5 w-1.5 animate-bounce rounded-full bg-gray-400"
                  style={{ animationDelay: "0.15s" }}
                />
                <span
                  className="h-1.5 w-1.5 animate-bounce rounded-full bg-gray-400"
                  style={{ animationDelay: "0.3s" }}
                />
              </div>
            </div>
          )}
        </div>

        {/* ERROR */}
        {error && (
          <div className="mx-5 mb-3 rounded-xl border border-red-200 bg-red-50 px-3.5 py-2.5 text-sm text-red-700">
            {error}
          </div>
        )}

        {/* INPUT BAR */}
        <div className="border-t border-gray-100 bg-gray-50/60 px-5 py-4">
          <div
            className="mx-auto flex max-w-3xl items-center gap-3 rounded-full border border-gray-200 bg-white px-4 py-2 shadow-[0_3px_14px_rgba(15,23,42,0.08)]"
          >
            <textarea
              ref={textareaRef}
              value={message}
              onChange={(event) => setMessage(event.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask your factory assistant..."
              rows={1}
              className="max-h-28 flex-1 resize-none border-0 bg-transparent px-2.5 py-2 text-sm text-gray-800 outline-none placeholder:text-gray-400"
            />
            <button
              onClick={sendMessage}
              disabled={loading || !message.trim()}
              className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl text-white transition-all hover:scale-105 disabled:cursor-not-allowed disabled:opacity-30 disabled:hover:scale-100"
              style={{ background: "linear-gradient(135deg, #4f46e5, #7c3aed)" }}
              title="Send"
            >
              <Send size={16} strokeWidth={2.25} />
            </button>
          </div>
          <p className="mt-2 text-center text-[11px] text-gray-400">
            Enter to send · Shift + Enter for a new line
          </p>
        </div>
      </div>
    </div>
  );
}

export default AIChat;