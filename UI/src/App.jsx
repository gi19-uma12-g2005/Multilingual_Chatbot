import { useState } from "react";
import { ReactTransliterate } from "react-transliterate";
import "react-transliterate/dist/index.css";
import "./App.css"; // 👈 New CSS file we’ll define below

export default function App() {
  const [messages, setMessages] = useState([
    { sender: "bot", text: "Hi! I'm your College Assistant. How can I help you today?" },
  ]);
  const [input, setInput] = useState("");
  const [language, setLanguage] = useState("en");
  const [loading, setLoading] = useState(false);

  const sendMessage = async () => {
    if (!input.trim()) return;

    const newUserMessage = { sender: "user", text: input };
    setMessages([...messages, newUserMessage]);
    setInput("");
    setLoading(true);

    try {
      const response = await fetch("http://localhost:5000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: input, lang: language }),
      });

      const data = await response.json();
      const botResponse = {
        sender: "bot",
        text: data.reply || "Sorry, I didn’t understand that.",
      };
      setMessages((prev) => [...prev, botResponse]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        { sender: "bot", text: "Server error. Please try again later." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter") sendMessage();
  };

  const translitLangMap = {
    en: "en",
    hi: "hi",
    mr: "mr",
    bn: "bn",
  };

  return (
    <div className="app-container">
      <div className="chat-box">
        {/* Header */}
        <div className="chat-header">
          <span>College Chatbot</span>
          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            className="lang-select"
          >
            <option value="en">English</option>
            <option value="hi">Hindi</option>
            <option value="mr">Marathi</option>
            <option value="bn">Bengali</option>
          </select>
        </div>

        {/* Chat Area */}
        <div className="chat-area">
          {messages.map((msg, index) => (
            <div
              key={index}
              className={`message ${msg.sender === "user" ? "user" : "bot"}`}
            >
              {msg.text}
            </div>
          ))}

          {loading && <div className="typing">Bot is typing...</div>}
        </div>

        {/* Input Area */}
        <div className="chat-input">
          <ReactTransliterate
            key={language}
            lang={translitLangMap[language]}
            value={input}
            onChangeText={setInput}
            onKeyDown={handleKeyDown}
            placeholder="Type your message..."
            className="input-field"
          />
          <button onClick={sendMessage} className="send-btn">
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
