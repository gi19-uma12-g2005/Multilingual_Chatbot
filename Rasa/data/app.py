from flask import Flask, request, jsonify
from flask_cors import CORS
from rasa.core.agent import Agent
import asyncio
import os

# Initialize Flask
app = Flask(__name__)
CORS(app)  #  Allow requests from your React frontend

# Paths to trained Rasa models
MODEL_PATHS = {
    "en": "D:/Umang_Coding/AI_chatbot/Rasa/data/models/model_en.tar.gz",
    "hi": "D:/Umang_Coding/AI_chatbot/Rasa/data/models/model_hi.tar.gz",
    "mr": "D:/Umang_Coding/AI_chatbot/Rasa/data/models/model_mr.tar.gz",
    "bn": "D:/Umang_Coding/AI_chatbot/Rasa/data/models/model_bn.tar.gz"
}

#  Cache loaded models to prevent reloading again and again
loaded_agents = {}

#  Default fallback model
FALLBACK_LANG = "en"

#  Single asyncio event loop
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)


def load_agent(language_code):
    """Loads and caches a Rasa agent (synchronously)."""
    if language_code in loaded_agents:
        return loaded_agents[language_code]

    model_path = MODEL_PATHS.get(language_code)
    if not model_path or not os.path.exists(model_path):
        raise FileNotFoundError(f"Model not found for language: {language_code}")

    print(f"Loading Rasa model for language: {language_code}")
    agent = Agent.load(model_path)  #  Synchronous load
    loaded_agents[language_code] = agent
    print(f" Model loaded successfully: {language_code}")
    return agent


@app.route("/chat", methods=["POST"])
def chat():
    """Handles chat requests and forwards messages to the correct Rasa model."""
    data = request.get_json(force=True)
    message = data.get("message", "").strip()
    language = data.get("lang", "en")

    if not message:
        return jsonify({"error": "Message is required"}), 400

    try:
        # Try loading the requested language model
        try:
            agent = load_agent(language)
        except Exception as e:
            print(f"Could not load model '{language}': {e}")
            if language != FALLBACK_LANG:
                print(f"Falling back to default model: {FALLBACK_LANG}")
                agent = load_agent(FALLBACK_LANG)
                language = FALLBACK_LANG
            else:
                return jsonify({"error": f"No available model for '{language}'"}), 500

        # Run Rasa model to get response
        responses = loop.run_until_complete(agent.handle_text(message))
        reply = " ".join([r.get("text", "") for r in responses if r.get("text")])

        return jsonify({
            "reply": reply or "No response from Rasa.",
            "language_used": language
        })

    except Exception as e:
        print(f"Error in /chat route: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/health", methods=["GET"])
def health():
    """Returns model availability and load status."""
    status = {}
    for lang, path in MODEL_PATHS.items():
        if not os.path.exists(path):
            status[lang] = "Missing"
        elif lang in loaded_agents:
            status[lang] = "Loaded in memory"
        else:
            status[lang] = "Available but not loaded"

    return jsonify({
        "status": "Flask + Rasa Dynamic Model API running",
        "models": status,
        "fallback": FALLBACK_LANG
    })


@app.route("/", methods=["GET"])
def home():
    """Root endpoint for quick API check."""
    return jsonify({
        "status": "API Live",
        "languages_supported": list(MODEL_PATHS.keys()),
        "loaded_models": list(loaded_agents.keys()),
        "hint": "Use POST /chat with JSON {message, lang}"
    })


if __name__ == "__main__":
    print("Starting Flask + Rasa Dynamic Server on port 5000...")
    app.run(host="0.0.0.0", port=5000, debug=True, threaded=True)
