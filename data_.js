const response = await fetch("http://127.0.0.1:8000/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message: text, language: language })
});
const data = await response.json();
appendMessage("bot", data.reply || "Sorry, I didn’t get that.");
