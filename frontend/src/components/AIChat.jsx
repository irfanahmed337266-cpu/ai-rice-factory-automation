import { useState } from "react";

function AIChat() {
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const sendMessage = async () => {
    const text = message.trim();

    if (!text || loading) {
      return;
    }

    setMessages((prev) => [
      ...prev,
      {
        role: "user",
        content: text,
      },
    ]);

    setMessage("");
    setError("");
    setLoading(true);

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/ai/chat",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Accept: "application/json",
          },
          body: JSON.stringify({
            message: text,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data?.detail || "AI request failed"
        );
      }

      const aiReply =
        data?.response ||
        data?.message ||
        data?.answer ||
        data?.reply ||
        JSON.stringify(data);

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: aiReply,
        },
      ]);
    } catch (err) {
      setError(
        err.message || "Unable to connect to AI Assistant"
      );
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
  };

  return (
    <div className="p-6">

      {/* HEADER */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold">
          AI Factory Assistant
        </h1>

        <p className="mt-1 text-gray-500">
          Ask about sales, purchases, stock, profit,
          receivables, payables and factory performance.
        </p>
      </div>


      {/* AI STATUS */}
      <div className="mb-5 flex items-center gap-3 rounded-xl border border-gray-200 bg-white p-4 shadow-sm">

        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-green-100">
          🤖
        </div>

        <div>
          <p className="font-semibold">
            AI System Online
          </p>

          <p className="text-sm text-gray-500">
            Factory intelligence is ready.
          </p>
        </div>

        <span className="ml-auto h-3 w-3 rounded-full bg-green-500" />
      </div>


      {/* QUICK QUESTIONS */}
      <div className="mb-5">

        <h2 className="mb-3 text-lg font-semibold">
          Quick Questions
        </h2>

        <div className="flex flex-wrap gap-2">

          {quickQuestions.map((question) => (
            <button
              key={question}
              onClick={() => askQuickQuestion(question)}
              className="rounded-full border border-gray-300 bg-white px-4 py-2 text-sm hover:bg-gray-50"
            >
              {question}
            </button>
          ))}

        </div>
      </div>


      {/* CHAT WINDOW */}
      <div className="flex min-h-[500px] flex-col rounded-xl border border-gray-200 bg-white shadow-sm">

        {/* MESSAGES */}
        <div className="flex-1 space-y-4 overflow-y-auto p-5">

          {messages.length === 0 && (
            <div className="flex min-h-[350px] items-center justify-center text-center">

              <div>
                <div className="mb-3 text-5xl">
                  🤖
                </div>

                <h2 className="text-xl font-semibold">
                  AI Factory Assistant
                </h2>

                <p className="mt-2 max-w-md text-gray-500">
                  Ask me anything about your rice factory.
                  I can help you understand sales,
                  purchases, stock, payments, profit and
                  overall factory performance.
                </p>
              </div>

            </div>
          )}


          {messages.map((item, index) => (
            <div
              key={index}
              className={`flex ${
                item.role === "user"
                  ? "justify-end"
                  : "justify-start"
              }`}
            >

              <div
                className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                  item.role === "user"
                    ? "bg-blue-600 text-white"
                    : "bg-gray-100 text-gray-900"
                }`}
              >
                <p className="whitespace-pre-wrap">
                  {item.content}
                </p>
              </div>

            </div>
          ))}


          {loading && (
            <div className="flex justify-start">

              <div className="rounded-2xl bg-gray-100 px-4 py-3 text-gray-600">
                AI is thinking...
              </div>

            </div>
          )}

        </div>


        {/* ERROR */}
        {error && (
          <div className="mx-5 mb-3 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            {error}
          </div>
        )}


        {/* INPUT */}
        <div className="border-t border-gray-200 p-4">

          <div className="flex gap-3">

            <textarea
              value={message}
              onChange={(event) =>
                setMessage(event.target.value)
              }
              onKeyDown={handleKeyDown}
              placeholder="Ask your factory assistant..."
              rows={2}
              className="flex-1 resize-none rounded-xl border border-gray-300 px-4 py-3 outline-none focus:border-blue-500"
            />

            <button
              onClick={sendMessage}
              disabled={loading || !message.trim()}
              className="rounded-xl bg-blue-600 px-6 font-semibold text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {loading ? "..." : "Send"}
            </button>

          </div>

          <p className="mt-2 text-xs text-gray-400">
            Press Enter to send. Shift + Enter for a new line.
          </p>

        </div>

      </div>

    </div>
  );
}

export default AIChat;