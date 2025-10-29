import { useState } from "react";

export default function App() {
  const [messages, setMessages] = useState([
    { sender: "bot", text: "👋 Hi! I'm your College Assistant. How can I help you today?" },
  ]);
  const [input, setInput] = useState("");
  const [language, setLanguage] = useState("en"); // Default: English
  const [loading, setLoading] = useState(false);

  // ✅ Send message to backend API
  const sendMessage = async () => {
    if (!input.trim()) return;

    const newUserMessage = { sender: "user", text: input };
    setMessages([...messages, newUserMessage]);
    setInput("");
    setLoading(true);

    try {
      // 🔗 Replace with your backend API (Rasa/Flask/FastAPI endpoint)
      const response = await fetch("http://localhost:5000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: input, lang: language }),
      });

      const data = await response.json();
      const botResponse = { sender: "bot", text: data.reply || "Sorry, I didn’t understand that." };
      setMessages((prev) => [...prev, botResponse]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        { sender: "bot", text: "⚠️ Server error. Please try again later." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  // Press Enter to send
  const handleKeyDown = (e) => {
    if (e.key === "Enter") sendMessage();
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gradient-to-br from-blue-50 to-blue-100">
      <div className="w-full max-w-md bg-white shadow-xl rounded-2xl overflow-hidden flex flex-col h-[80vh]">

        {/* 🔵 Header */}
        <div className="bg-blue-600 text-white p-4 text-center font-semibold text-lg flex justify-between items-center">
          <span>🎓 College Chatbot</span>

          {/* 🌐 Language Selector */}
          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            className="bg-blue-700 text-white text-sm rounded-lg px-2 py-1 focus:outline-none"
          >
            <option value="en">English</option>
            <option value="hi">Hindi</option>
            <option value="mr">Marathi</option>
            <option value="rj">Rajasthani</option>
            <option value="bn">Bengali</option>
          </select>
        </div>

        {/* 💬 Chat Area */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-gray-50">
          {messages.map((msg, index) => (
            <div
              key={index}
              className={`flex ${
                msg.sender === "user" ? "justify-end" : "justify-start"
              }`}
            >
              <div
                className={`px-4 py-2 rounded-2xl max-w-[75%] text-sm ${
                  msg.sender === "user"
                    ? "bg-blue-500 text-white rounded-br-none"
                    : "bg-gray-200 text-gray-900 rounded-bl-none"
                }`}
              >
                {msg.text}
              </div>
            </div>
          ))}

          {loading && (
            <div className="text-gray-400 text-sm italic">🤖 Bot is typing...</div>
          )}
        </div>

        {/* ⌨️ Input Section */}
        <div className="p-3 bg-white border-t flex items-center space-x-2">
          <input
            type="text"
            placeholder="Type your message..."
            className="flex-1 border rounded-xl px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
          />
          <button
            onClick={sendMessage}
            className="bg-blue-500 hover:bg-blue-600 text-white rounded-xl px-4 py-2 text-sm font-medium"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
