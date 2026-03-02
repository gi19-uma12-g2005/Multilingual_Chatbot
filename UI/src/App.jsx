import { useState } from "react";
import { ReactTransliterate } from "react-transliterate";
import "react-transliterate/dist/index.css";
import "./App.css";

export default function App() {
  const [messages, setMessages] = useState([
    { sender: "bot", text: "Hi! I'm your College Assistant. How can I help you today?" },
  ]);
  const [input, setInput] = useState("");
  const [language, setLanguage] = useState("en");
  const [loading, setLoading] = useState(false);

  // Helper: remove emojis from text
  const removeEmojis = (text = "") => {
    const emojiRegex = /[\u{1F600}-\u{1F64F}\u{1F300}-\u{1F5FF}\u{1F680}-\u{1F6FF}\u{1F700}-\u{1F77F}\u{1F780}-\u{1F7FF}\u{1F800}-\u{1F8FF}\u{1F900}-\u{1F9FF}\u{1FA00}-\u{1FA6F}\u{1FA70}-\u{1FAFF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}]/gu;
    return String(text).replace(emojiRegex, "");
  };

  // 🔹 Send message to backend Flask API
  const sendMessage = async () => {
    if (!input.trim()) return;

    const newUserMessage = { sender: "user", text: input };
    setMessages((prev) => [...prev, newUserMessage]);
    setInput("");
    setLoading(true);

    console.log("Sending message:", input, "Language:", language);

    try {
      const response = await fetch("http://127.0.0.1:5000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: input, lang: language }),
      });

      let data = { reply: "" };
      if (response.ok) {
        const ct = response.headers.get("content-type") || "";
        if (ct.includes("application/json")) {
          data = await response.json();
        } else {
          // Backend returned plain text (or HTML); use as reply
          const text = await response.text();
          data = { reply: text };
        }
        console.log("Received response data:", data);
      } else {
        // Non-2xx response: read text to show meaningful message
        const text = await response.text();
        data = { reply: `Server error: ${text}` };
      }

      const botText = removeEmojis(data.reply || "Sorry, I didn't understand that.");
      const botResponse = {
        sender: "bot",
        text: botText,
      };
      setMessages((prev) => [...prev, botResponse]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        { sender: "bot", text: removeEmojis("Server error. Please try again later.") },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      // Prevent default newline behavior when not using Shift+Enter
      e.preventDefault();
      sendMessage();
    }
  };

  // 🔹 Detect and render clickable links in bot messages
  const renderMessage = (text) => {
    if (!text) return null;
    // Use non-global regex to avoid test() stateful behavior
    const urlRegex = /(https?:\/\/[^\s]+)/;
    const parts = text.split(urlRegex);

    return parts.map((part, index) => {
      if (urlRegex.test(part)) {
        return (
          <a
            key={index}
            href={part}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-600 underline hover:text-blue-800 wrap-break-word"
          >
            {part}
          </a>
        );
      } else {
        return <span key={index}>{part}</span>;
      }
    });
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
              {msg.sender === "bot" ? renderMessage(msg.text) : msg.text}
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