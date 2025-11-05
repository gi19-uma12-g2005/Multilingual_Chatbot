from flask import Flask, request, jsonify
from flask_cors import CORS
from rasa.core.agent import Agent
import asyncio
import os
import threading

# 🚀 Initialize Flask
app = Flask(__name__)
CORS(app)  # Allow requests from your React frontend

# 🧠 Paths to trained Rasa models
MODEL_PATHS = {
    "en": "D:/Umang_Coding/AI_chatbot/Rasa/data/models/model_en.tar.gz",
    "hi": "D:/Umang_Coding/AI_chatbot/Rasa/data/models/model_hi.tar.gz",
    "mr": "D:/Umang_Coding/AI_chatbot/Rasa/data/models/model_mr.tar.gz",
    "bn": "D:/Umang_Coding/AI_chatbot/Rasa/data/models/model_bn.tar.gz"
}

# Cache for loaded models to prevent reloading
loaded_agents = {}
FALLBACK_LANG = "en"

# Create a single event loop for all async Rasa operations
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)


def load_agent(language_code):
    """Load and cache a Rasa agent for a specific language."""
    if language_code in loaded_agents:
        return loaded_agents[language_code]

    model_path = MODEL_PATHS.get(language_code)
    if not model_path or not os.path.exists(model_path):
        raise FileNotFoundError(f"❌ Model not found for language: {language_code}")

    print(f"🧠 Loading Rasa model for '{language_code}'...")
    agent = Agent.load(model_path)  # synchronous loading
    loaded_agents[language_code] = agent
    print(f"✅ Model for '{language_code}' loaded successfully.")
    return agent


def preload_all_models():
    """Preload all Rasa models asynchronously in a background thread."""
    print("🚀 Preloading all Rasa models in background...")
    for lang in MODEL_PATHS.keys():
        try:
            load_agent(lang)
        except Exception as e:
            print(f"⚠ Could not load model '{lang}': {e}")
    print("🎯 All models are ready to chat!")


@app.route("/chat", methods=["POST"])
def chat():
    """Handles incoming chat messages and routes to the correct model."""
    data = request.get_json(force=True)
    message = data.get("message", "").strip()
    language = data.get("lang", "en")

    if not message:
        return jsonify({"error": "Message is required"}), 400

    try:
        # Try loading the requested model
        try:
            agent = load_agent(language)
        except Exception as e:
            print(f"⚠ Could not load model '{language}': {e}")
            if language != FALLBACK_LANG:
                print(f"↩ Falling back to default model: {FALLBACK_LANG}")
                agent = load_agent(FALLBACK_LANG)
                language = FALLBACK_LANG
            else:
                return jsonify({"error": f"No model found for '{language}'"}), 500

        # 🧠 Use the loaded model to generate response
        responses = loop.run_until_complete(agent.handle_text(message))
        reply = " ".join([r.get("text", "") for r in responses if r.get("text")])

        return jsonify({
            "reply": reply or "🤖 No response from Rasa.",
            "language_used": language
        })

    except Exception as e:
        print(f"❌ Error in /chat: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/", methods=["GET"])
def home():
    """Root route for checking API status."""
    return jsonify({
        "status": "✅ Flask + Rasa API is Live",
        "languages_supported": list(MODEL_PATHS.keys()),
        "loaded_models": list(loaded_agents.keys()),
        "hint": "Use POST /chat with JSON {message, lang}"
    })


if __name__ == "__main__":
    print("🚀 Starting Flask + Rasa Dynamic Server...")
    # preload models in background (non-blocking)
    threading.Thread(target=preload_all_models, daemon=True).start()
    # run Flask server
    app.run(host="0.0.0.0", port=5000, debug=True, threaded=True)