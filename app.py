from flask import Flask, request, jsonify, render_template_string
import requests
import hmac
import hashlib
import time
import os
from datetime import datetime

app = Flask(__name__)

# ==========================
# BINGX API - С ЗАПАСНЫМИ ЗНАЧЕНИЯМИ
# ==========================
BINGX_API_KEY = os.getenv("BINGX_API_KEY", "tfi2cWlGNK9eSpDJlxNks2w7DBiT6lTlUiXLjkBQhe7sIgVv7HKWiByVhDSagmrZBSgb8Hoaog1N4HzYffQ")
BINGX_SECRET_KEY = os.getenv("BINGX_SECRET_KEY", "SnNoEvoc1ZBhwHYMzi1KfAIvvgnI8eWs6b4fyjo9i7u0pcsHijJ7YIEngeHUVD19YxLeyrp2yE9UPjYAqM65w")
BINGX_BASE_URL = "https://open-api.bingx.com"

# ==========================
# TELEGRAM - С ЗАПАСНЫМИ ЗНАЧЕНИЯМИ
# ==========================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8337671886:AAFQk7A6ZYhgu63l9C2cmAj3meTJa7RD3b4")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "5411759224")

# ==========================
# НАСТРОЙКИ
# ==========================
POSITION_SIZE_USDT = 5
LEVERAGE = 10
RECV_WINDOW = 60000
ALLOWED_TIMEFRAMES = [15]

# ==========================
# СИМВОЛЫ
# ==========================
SYMBOL_MAP = {
    "BTCUSDT": "BTC-USDT", "BTCUSDT.P": "BTC-USDT",
    "ETHUSDT": "ETH-USDT", "ETHUSDT.P": "ETH-USDT",
    "BNBUSDT": "BNB-USDT", "BNBUSDT.P": "BNB-USDT",
    "SOLUSDT": "SOL-USDT", "SOLUSDT.P": "SOL-USDT",
    "XRPUSDT": "XRP-USDT", "XRPUSDT.P": "XRP-USDT",
    "ADAUSDT": "ADA-USDT", "ADAUSDT.P": "ADA-USDT",
    "DOGEUSDT": "DOGE-USDT", "DOGEUSDT.P": "DOGE-USDT",
    "AVAXUSDT": "AVAX-USDT", "AVAXUSDT.P": "AVAX-USDT",
    "MATICUSDT": "MATIC-USDT", "MATICUSDT.P": "MATIC-USDT",
    "DOTUSDT": "DOT-USDT", "DOTUSDT.P": "DOT-USDT",
    "TRXUSDT": "TRX-USDT", "TRXUSDT.P": "TRX-USDT",
    "LINKUSDT": "LINK-USDT", "LINKUSDT.P": "LINK-USDT",
    "ARBUSDT": "ARB-USDT", "ARBUSDT.P": "ARB-USDT",
    "PEPEUSDT": "PEPE-USDT", "PEPEUSDT.P": "PEPE-USDT",
    "SHIBUSDT": "SHIB-USDT", "SHIBUSDT.P": "SHIB-USDT",
    "FLOKIUSDT": "FLOKI-USDT", "FLOKIUSDT.P": "FLOKI-USDT",
    "FTMUSDT": "FTM-USDT", "FTMUSDT.P": "FTM-USDT",
    "NEARUSDT": "NEAR-USDT", "NEARUSDT.P": "NEAR-USDT",
    "ATOMUSDT": "ATOM-USDT", "ATOMUSDT.P": "ATOM-USDT",
    "OPUSDT": "OP-USDT", "OPUSDT.P": "OP-USDT",
    "APTUSDT": "APT-USDT", "APTUSDT.P": "APT-USDT",
    "IMXUSDT": "IMX-USDT", "IMXUSDT.P": "IMX-USDT",
    "LDOUSDT": "LDO-USDT", "LDOUSDT.P": "LDO-USDT",
    "WLDUSDT": "WLD-USDT", "WLDUSDT.P": "WLD-USDT",
    "INJUSDT": "INJ-USDT", "INJUSDT.P": "INJ-USDT",
    "SUIUSDT": "SUI-USDT", "SUIUSDT.P": "SUI-USDT",
}

MIN_QUANTITY = {
    "BTC-USDT": 0.001, "ETH-USDT": 0.01, "BNB-USDT": 0.01,
    "SOL-USDT": 0.1, "XRP-USDT": 1, "ADA-USDT": 1,
    "DOGE-USDT": 1, "AVAX-USDT": 0.1, "MATIC-USDT": 1,
    "DOT-USDT": 0.1, "TRX-USDT": 1, "LINK-USDT": 0.1,
    "ARB-USDT": 1, "PEPE-USDT": 100000, "SHIB-USDT": 100000,
    "FLOKI-USDT": 10000, "FTM-USDT": 1, "NEAR-USDT": 1,
    "ATOM-USDT": 1, "OP-USDT": 1, "APT-USDT": 0.1,
    "IMX-USDT": 1, "LDO-USDT": 1, "WLD-USDT": 1,
    "INJ-USDT": 0.1, "SUI-USDT": 1,
}

QUANTITY_PRECISION = {
    "BTC-USDT": 3, "ETH-USDT": 2, "BNB-USDT": 2,
    "SOL-USDT": 2, "XRP-USDT": 0, "ADA-USDT": 0,
    "DOGE-USDT": 0, "AVAX-USDT": 2, "MATIC-USDT": 0,
    "DOT-USDT": 2, "TRX-USDT": 0, "LINK-USDT": 2,
    "ARB-USDT": 0, "PEPE-USDT": 0, "SHIB-USDT": 0,
    "FLOKI-USDT": 0, "FTM-USDT": 0, "NEAR-USDT": 1,
    "ATOM-USDT": 1, "OP-USDT": 0, "APT-USDT": 2,
    "IMX-USDT": 0, "LDO-USDT": 0, "WLD-USDT": 0,
    "INJ-USDT": 2, "SUI-USDT": 0,
}

def send_telegram(message: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram отключен")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print(f"Ошибка Telegram: {e}")

def sign(params: dict) -> str:
    qs = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
    return hmac.new(BINGX_SECRET_KEY.encode(), qs.encode(), hashlib.sha256).hexdigest()

def bingx(method, endpoint, params=None):
    if params is None:
        params = {}
    params["timestamp"] = int(time.time() * 1000)
    params["recvWindow"] = RECV_WINDOW
    params["signature"] = sign(params)
    headers = {"X-BX-APIKEY": BINGX_API_KEY}
    url = BINGX_BASE_URL + endpoint
    try:
        if method == "GET":
            r = requests.get(url, params=params, headers=headers, timeout=10)
        else:
            r = requests.post(url, params=params, headers=headers, timeout=10)
        return r.json()
    except Exception as e:
        print(f"BingX error: {e}")
        return {"code": -1, "msg": str(e)}

def get_price(symbol):
    r = bingx("GET", "/openApi/swap/v2/quote/price", {"symbol": symbol})
    if r.get("code") == 0:
        return float(r["data"]["price"])
    return None

def set_leverage(symbol):
    return bingx("POST", "/openApi/swap/v2/trade/leverage", {"symbol": symbol, "side": "BOTH", "leverage": LEVERAGE})

def get_positions():
    return bingx("GET", "/openApi/swap/v2/user/positions", {})

def has_position(symbol, side):
    r = get_positions()
    if r.get("code") != 0:
        return False
    for p in r.get("data", []):
        if p["symbol"] == symbol:
            amt = float(p["positionAmt"])
            if side == "BUY" and amt > 0:
                return True
            if side == "SELL" and amt < 0:
                return True
    return False

def calculate_quantity(symbol, usdt_amount, price):
    if price <= 0:
        return 0
    raw_qty = usdt_amount / price
    precision = QUANTITY_PRECISION.get(symbol, 2)
    qty = round(raw_qty, precision)
    min_qty = MIN_QUANTITY.get(symbol, 0.01)
    if qty < min_qty:
        print(f"⚠️ Qty {qty} < min {min_qty} для {symbol}")
        return 0
    return qty

def place_order(symbol, side, qty):
    return bingx("POST", "/openApi/swap/v2/trade/order", {
        "symbol": symbol, "side": side,
        "positionSide": "LONG" if side == "BUY" else "SHORT",
        "type": "MARKET", "quantity": str(qty)
    })

def place_sl_tp(symbol, side, sl, tp):
    close_side = "SELL" if side == "BUY" else "BUY"
    pos_side = "LONG" if side == "BUY" else "SHORT"
    bingx("POST", "/openApi/swap/v2/trade/order", {
        "symbol": symbol, "side": close_side, "positionSide": pos_side,
        "type": "STOP_MARKET", "stopPrice": str(sl), "closePosition": "true"
    })
    bingx("POST", "/openApi/swap/v2/trade/order", {
        "symbol": symbol, "side": close_side, "positionSide": pos_side,
        "type": "TAKE_PROFIT_MARKET", "stopPrice": str(tp), "closePosition": "true"
    })

HTML_PAGE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>BingX Bot</title>
    <style>
        body{font-family:Arial;background:#121212;color:#e0e0e0;text-align:center;padding:50px}
        .container{max-width:600px;margin:0 auto;background:#1e1e1e;padding:30px;border-radius:15px}
        h1{color:#00ff00}
        .ok{color:#00ff00}
        .warn{color:#ffff00}
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 BingX Trading Bot</h1>
        <p>Бот работает и готов принимать сигналы</p>
        <div>
            Размер: <strong>{{position_size}} USDT</strong> × {{leverage}}x<br>
            ТФ: <strong>{{allowed_tf}}</strong> мин<br>
            Telegram: <span class="{{tg_status}}">{{tg_text}}</span>
        </div>
    </div>
</body>
</html>
"""

@app.route("/")
def index():
    tg_ok = TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID
    return render_template_string(HTML_PAGE, 
        position_size=POSITION_SIZE_USDT, leverage=LEVERAGE,
        allowed_tf=", ".join(map(str, ALLOWED_TIMEFRAMES)),
        tg_status="ok" if tg_ok else "warn",
        tg_text="Включены ✅" if tg_ok else "Не настроены ⚠️"
    )

@app.route("/webhook", methods=["POST"])
def webhook():
    d = request.json
    if not d:
        return jsonify({"error": "no json"}), 400
    tf = int(d.get("tf", 0))
    tv_symbol = d.get("symbol", "UNKNOWN")
    direction = d.get("direction", "").upper()
    signal = d.get("signal", "N/A")
    base_msg = f"🚨 {signal}\n{tv_symbol} {direction} {tf}m\n"
    if tf not in ALLOWED_TIMEFRAMES:
        send_telegram(base_msg + "❌ Запрещённый ТФ")
        return jsonify({"status": "ignored_tf"})
    if tv_symbol not in SYMBOL_MAP:
        send_telegram(base_msg + "❌ Символ не поддерживается")
        return jsonify({"error": "symbol not supported"}), 400
    symbol = SYMBOL_MAP[tv_symbol]
    side = "BUY" if direction == "LONG" else "SELL"
    sl_raw = d.get("sl", "na")
    tp_raw = d.get("tp", "na")
    if sl_raw == "na" or tp_raw == "na":
        send_telegram(base_msg + "⚠️ Без SL/TP")
        sl = None
        tp = None
    else:
        try:
            sl = float(sl_raw)
            tp = float(tp_raw)
        except:
            send_telegram(base_msg + "❌ Некорректные SL/TP")
            return jsonify({"error": "invalid sl/tp"}), 400
    if has_position(symbol, side):
        send_telegram(base_msg + "⚠️ Позиция уже открыта")
        return jsonify({"status": "position_exists"})
    price = get_price(symbol)
    if not price:
        send_telegram(base_msg + "❌ Не получена цена")
        return jsonify({"error": "price failed"}), 500
    qty = calculate_quantity(symbol, POSITION_SIZE_USDT, price)
    if qty <= 0:
        send_telegram(base_msg + f"❌ Размер слишком мал: {qty}")
        return jsonify({"error": "qty too small"}), 400
    send_telegram(base_msg + f"💼 Открываем {symbol} {qty}")
    set_leverage(symbol)
    order = place_order(symbol, side, qty)
    if order.get("code") == 0:
        if sl and tp:
            place_sl_tp(symbol, side, sl, tp)
        send_telegram(f"✅ {symbol} {side} открыта!")
        status = "success"
    else:
        send_telegram(f"❌ ОШИБКА: {order.get('msg')}")
        status = "error"
    return jsonify({"symbol": symbol, "qty": qty, "status": status})

@app.route("/test")
def test():
    result = bingx("GET", "/openApi/swap/v2/user/balance", {})
    send_telegram(f"🧪 Тест: {result.get('code')} {result.get('msg')}")
    return jsonify(result)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
