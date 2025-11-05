from flask import Flask, request
import os
import requests

app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Бот работает на Render!"

@app.route('/test')
def test():
    return "✅ Test OK — бот на связи!"

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    token = os.environ.get("TELEGRAM_TOKEN")
    chat_id = os.environ.get("CHAT_ID")

    if data and "signal" in data:
        text = f"Signal: {data['signal']}\nSymbol: {data.get('symbol')}\nPrice: {data.get('price')}"
        requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text}
        )
        return "OK", 200

    return "No data", 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
