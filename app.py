from flask import Flask, request
import requests
from datetime import datetime

app = Flask(__name__)

BOT_TOKEN = "8337671886:AAFQk7A6ZYhgu63l9C2cmAj3meTJa7RD3b4"
CHAT_ID = "5411759224"


def send_to_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text}
    r = requests.post(url, json=payload)
    print(">>> Ответ Telegram:", r.status_code, r.text)
@app.route('/')
def home():
    return "Bot is running!", 200

@app.route('/test')
def test():
    return "Webhook tester OK", 200

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json(force=True, silent=True)

        if not data:
            raw = request.get_data(as_text=True)
            print("!!! Нет JSON. Сырое тело:", raw)
            return "No JSON", 400

        signal = data.get('signal', 'N/A')
        direction = data.get('direction', 'N/A')
        symbol = data.get('symbol', 'N/A')
        price = data.get('price', 'N/A')
        tp1 = data.get('tp1', 'N/A')
        tp2 = data.get('tp2', 'N/A')
        sl = data.get('sl', 'N/A')
        tf = data.get('tf', 'N/A')

        message = (
            f"{signal}\n\n"
            f"Символ: {symbol}\n"
            f"Направление: {direction}\n"
            f"Цена входа: {price}\n"
            f"TF: {tf}m\n\n"
            f"TP1: {tp1}\n"
            f"TP2: {tp2}\n"
            f"SL: {sl}\n\n"
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

        with open("signals.log", "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now()}] {data}\n")

        print(">>> Получено сообщение:", data)
        send_to_telegram(message)

        return "OK", 200

    except Exception as e:
        print("!!! Ошибка:", e)
        return "Error", 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)



