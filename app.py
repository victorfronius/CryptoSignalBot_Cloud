from flask import Flask, request
import requests
import os

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get("8337671886:AAFQk7A6ZYhgu63l9C2cmAj3meTJa7RD3b4")
CHAT_ID = os.environ.get("5411759224")

@app.route('/')
def home():
    return "CryptoSignalBot online ✅"

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json(force=True)
    text = f"📈 {data}"
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text}
    requests.post(url, json=payload)
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))