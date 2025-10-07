import subprocess
import time
from threading import Thread
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

# -------------------------
# Flask Backend Setup
# -------------------------
app = Flask(__name__)
CORS(app)

# Rasa servers mapping
RASA_SERVERS = {
    "english": "http://localhost:5005/webhooks/rest/webhook",
    "hindi": "http://localhost:5006/webhooks/rest/webhook",
    "marathi": "http://localhost:5007/webhooks/rest/webhook",
    "bangla": "http://localhost:5008/webhooks/rest/webhook"
}

@app.route("/")
def index():
    return "Flask backend running. Use POST /api/chat."

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.json
    message = data.get("message")
    language = data.get("language")

    if not message or language not in RASA_SERVERS:
        return jsonify({"reply": "Invalid request"}), 400

    rasa_url = RASA_SERVERS[language]
    try:
        res = requests.post(rasa_url, json={"sender": "user", "message": message})
        res_json = res.json()
        reply = res_json[0].get("text", "Sorry, I didn't understand that.") if res_json else "No response from bot."
        return jsonify({"reply": reply})
    except Exception as e:
        return jsonify({"reply": f"Error: {str(e)}"}), 500

# -------------------------
# Function to start Rasa server
# -------------------------
def start_rasa_server(model_folder, port):
    subprocess.Popen([
        "rasa", "run",
        "--model", model_folder,
        "--enable-api",
        "--cors", "*",
        "--port", str(port)
    ], cwd=model_folder)

# -------------------------
# Start all Rasa servers
# -------------------------
def start_all_rasa():
    servers = {
        "english": (r"D:\Umang_Coding\AI_chatbot\Rasa\data\en", 5005),
        "hindi": (r"D:\Umang_Coding\AI_chatbot\Rasa\data\hn", 5006),
        "marathi": (r"D:\Umang_Coding\AI_chatbot\Rasa\data\mar", 5007),
        "bangla": (r"D:\Umang_Coding\AI_chatbot\Rasa\data\ben", 5008)
    }
    for lang, (folder, port) in servers.items():
        print(f"Starting {lang} server on port {port}...")
        Thread(target=start_rasa_server, args=(folder, port)).start()
        time.sleep(3)  # give time to start

# -------------------------
# Main
# -------------------------
if __name__ == "__main__":
    # Start Rasa servers
    start_all_rasa()
    print("All Rasa servers started.")

    # Start Flask backend
    app.run(host="127.0.0.1", port=8000, debug=True)
