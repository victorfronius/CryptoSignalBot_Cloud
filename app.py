from flask import Flask, request
import requests
from datetime import datetime

app = Flask(__name__)

BOT_TOKEN = "8337671896:AAFQk7A6ZYhgu631GC2emAj3meTJa7RD3B4"
CHAT_ID = "5411759224"

def send_to_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    r = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
    print("📤 Ответ Telegram:", r.status_code, r.text)

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        if request.is_json:
            data = request.get_json()
            
            # Получаем данные из JSON
            signal = data.get('signal', 'N/A')
            direction = data.get('direction', 'N/A')
            symbol = data.get('symbol', 'N/A')
            price = data.get('price', 'N/A')
            tp1 = data.get('tp1', 'N/A')
            tp2 = data.get('tp2', 'N/A')
            sl = data.get('sl', 'N/A')
            tf = data.get('tf', 'N/A')
            
            # Эмодзи для сигналов
            if "STRONG" in signal:
                emoji = "🔥🟢" if direction == "LONG" else "🔥🔴"
            else:
                emoji = "🟢" if direction == "LONG" else "🔴"
            
            # Формируем красивое сообщение
            message = f"""{emoji} <b>{signal}</b>

📊 <b>Символ:</b> {symbol}
📈 <b>Направление:</b> {direction}
💰 <b>Цена входа:</b> {price}
⏱ <b>Таймфрейм:</b> {tf}m

🎯 <b>Take Profit:</b>
   TP1: {tp1}
   TP2: {tp2}

🛑 <b>Stop Loss:</b> {sl}

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
            
            # Сохраняем в файл log
            with open("signals.log", "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {data}\n")
            
            print("✅ Получено сообщение:", data)
            send_to_telegram(message)
            return "OK", 200
        else:
            return "Invalid data", 400
            
    except Exception as e:
        print("❌ Ошибка:", e)
        return "Error", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

