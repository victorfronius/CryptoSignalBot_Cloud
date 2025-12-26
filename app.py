from flask import Flask, request, jsonify
import requests
import hmac
import hashlib
import time

app = Flask(__name__)

BINGX_API_KEY = "BMWtI97RFrKmpBEQoOvcxWA6oeL60gnWqrUqSeDNbALuBgmlyYw4KfYFfBfSqNptKN0U5jhOO4gQvOs0qiPA"
BINGX_SECRET_KEY = "qvkjbJn2yIGHaTXvfUu9a9o01UgC2S88xaDhkO2buJVdDik25ovPyzkQwCZ6O9Je6h7mKF5nBnM97YVgfvUQ"
BINGX_BASE_URL = "https://open-api.bingx.com"
TELEGRAM_BOT_TOKEN = "8337671886:AAFQk7A6ZYhgu63l9C2cmAj3meTJa7RD3b4"
TELEGRAM_CHAT_ID = "5411759224"

POSITION_SIZE_USDT = 5  # Для обычных монет
LEVERAGE = 10
ALLOWED_TIMEFRAMES = [15]

# Мемкоины с увеличенным размером позиции
MEME_COINS = {
    "PEPE-USDT": 50,   # 50 USDT для PEPE
    "SHIB-USDT": 50,   # 50 USDT для SHIB
    "FLOKI-USDT": 50,  # 50 USDT для FLOKI
}

SYMBOL_MAP = {
    "BTCUSDT": "BTC-USDT", "BTCUSDT.P": "BTC-USDT", "ETHUSDT": "ETH-USDT", "ETHUSDT.P": "ETH-USDT",
    "BNBUSDT": "BNB-USDT", "BNBUSDT.P": "BNB-USDT", "SOLUSDT": "SOL-USDT", "SOLUSDT.P": "SOL-USDT",
    "XRPUSDT": "XRP-USDT", "XRPUSDT.P": "XRP-USDT", "ADAUSDT": "ADA-USDT", "ADAUSDT.P": "ADA-USDT",
    "DOGEUSDT": "DOGE-USDT", "DOGEUSDT.P": "DOGE-USDT", "AVAXUSDT": "AVAX-USDT", "AVAXUSDT.P": "AVAX-USDT",
    "MATICUSDT": "MATIC-USDT", "MATICUSDT.P": "MATIC-USDT", "DOTUSDT": "DOT-USDT", "DOTUSDT.P": "DOT-USDT",
    "TRXUSDT": "TRX-USDT", "TRXUSDT.P": "TRX-USDT", "LINKUSDT": "LINK-USDT", "LINKUSDT.P": "LINK-USDT",
    "ARBUSDT": "ARB-USDT", "ARBUSDT.P": "ARB-USDT", "PEPEUSDT": "PEPE-USDT", "PEPEUSDT.P": "PEPE-USDT",
    "SHIBUSDT": "SHIB-USDT", "SHIBUSDT.P": "SHIB-USDT", "FLOKIUSDT": "FLOKI-USDT", "FLOKIUSDT.P": "FLOKI-USDT",
    "FTMUSDT": "FTM-USDT", "FTMUSDT.P": "FTM-USDT", "NEARUSDT": "NEAR-USDT", "NEARUSDT.P": "NEAR-USDT",
    "ATOMUSDT": "ATOM-USDT", "ATOMUSDT.P": "ATOM-USDT", "OPUSDT": "OP-USDT", "OPUSDT.P": "OP-USDT",
    "APTUSDT": "APT-USDT", "APTUSDT.P": "APT-USDT", "IMXUSDT": "IMX-USDT", "IMXUSDT.P": "IMX-USDT",
    "LDOUSDT": "LDO-USDT", "LDOUSDT.P": "LDO-USDT", "WLDUSDT": "WLD-USDT", "WLDUSDT.P": "WLD-USDT",
    "INJUSDT": "INJ-USDT", "INJUSDT.P": "INJ-USDT", "SUIUSDT": "SUI-USDT", "SUIUSDT.P": "SUI-USDT",
}

MIN_QTY = {
    "BTC-USDT": 0.001, "ETH-USDT": 0.01, "BNB-USDT": 0.01, "SOL-USDT": 0.1, "XRP-USDT": 1, "ADA-USDT": 1,
    "DOGE-USDT": 1, "AVAX-USDT": 0.1, "MATIC-USDT": 1, "DOT-USDT": 0.1, "TRX-USDT": 1, "LINK-USDT": 0.1,
    "ARB-USDT": 1, "PEPE-USDT": 100000, "SHIB-USDT": 100000, "FLOKI-USDT": 10000, "FTM-USDT": 1, "NEAR-USDT": 1,
    "ATOM-USDT": 1, "OP-USDT": 1, "APT-USDT": 0.1, "IMX-USDT": 1, "LDO-USDT": 1, "WLD-USDT": 1,
    "INJ-USDT": 0.1, "SUI-USDT": 1,
}

QTY_PREC = {
    "BTC-USDT": 3, "ETH-USDT": 2, "BNB-USDT": 2, "SOL-USDT": 2, "XRP-USDT": 0, "ADA-USDT": 0,
    "DOGE-USDT": 0, "AVAX-USDT": 2, "MATIC-USDT": 0, "DOT-USDT": 2, "TRX-USDT": 0, "LINK-USDT": 2,
    "ARB-USDT": 0, "PEPE-USDT": 0, "SHIB-USDT": 0, "FLOKI-USDT": 0, "FTM-USDT": 0, "NEAR-USDT": 1,
    "ATOM-USDT": 1, "OP-USDT": 0, "APT-USDT": 2, "IMX-USDT": 0, "LDO-USDT": 0, "WLD-USDT": 0,
    "INJ-USDT": 2, "SUI-USDT": 0,
}

def tg(msg):
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        try:
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", 
                data={"chat_id": TELEGRAM_CHAT_ID, "text": msg}, timeout=5)
        except:
            pass

def praseParam(p):
    s = sorted(p)
    return "&".join([f"{x}={p[x]}" for x in s]) + "&timestamp=" + str(p["timestamp"])

def bx(m, e, p=None):
    if not p:
        p = {}
    p["timestamp"] = int(time.time() * 1000)
    pay = praseParam(p)
    sig = hmac.new(BINGX_SECRET_KEY.encode(), pay.encode(), hashlib.sha256).hexdigest()
    url = f"{BINGX_BASE_URL}{e}?{pay}&signature={sig}"
    h = {"X-BX-APIKEY": BINGX_API_KEY}
    try:
        r = requests.get(url, headers=h, timeout=10) if m == "GET" else requests.post(url, headers=h, timeout=10)
        return r.json()
    except:
        return {"code": -1}

@app.route("/")
def home():
    return "<h1>🚀 BingX Bot</h1><p>One-way mode + SL/TP</p><a href='/test'>Test</a>"

@app.route("/test")
def test():
    r = bx("GET", "/openApi/swap/v2/user/balance", {})
    tg(f"🧪 {r.get('code')} {r.get('msg', 'OK')}")
    return jsonify(r)

@app.route("/webhook", methods=["POST"])
def webhook():
    d = request.json
    if not d:
        return jsonify({"error": "no json"}), 400
    
    tf = int(d.get("tf", 0))
    sym = d.get("symbol", "?")
    dir = d.get("direction", "").upper()
    sig = d.get("signal", "?")
    sl_raw = d.get("sl", "na")
    tp_raw = d.get("tp", "na")
    
    m = f"🚨 {sig}\n{sym} {dir} {tf}m\n"
    
    if tf not in ALLOWED_TIMEFRAMES:
        tg(m + "❌ TF")
        return jsonify({"s": "tf"})
    
    if sym not in SYMBOL_MAP:
        tg(m + "❌ SYM")
        return jsonify({"e": "sym"}), 400
    
    s = SYMBOL_MAP[sym]
    si = "BUY" if dir == "LONG" else "SELL"
    
    # Проверка SL/TP
    if sl_raw == "na" or tp_raw == "na":
        tg(m + "⚠️ Нет SL/TP - пропускаем")
        return jsonify({"s": "no_sltp"})
    
    try:
        sl = float(sl_raw)
        tp = float(tp_raw)
    except:
        tg(m + "❌ Некорректные SL/TP")
        return jsonify({"e": "invalid_sltp"}), 400
    
    # Проверка открытых позиций
    pos = bx("GET", "/openApi/swap/v2/user/positions", {})
    if pos.get("code") == 0:
        for p in pos.get("data", []):
            if p["symbol"] == s:
                amt = float(p.get("positionAmt", 0))
                if amt != 0:
                    tg(m + f"⚠️ Позиция уже есть: {amt}")
                    return jsonify({"s": "exists"})
    
    # Получение цены
    pr = bx("GET", "/openApi/swap/v2/quote/price", {"symbol": s})
    if pr.get("code") != 0:
        tg(m + "❌ Цена")
        return jsonify({"e": "pr"}), 500
    
    price = float(pr["data"]["price"])
    
    # Размер позиции (увеличенный для мемкоинов)
    pos_size = MEME_COINS.get(s, POSITION_SIZE_USDT)
    
    qty = round(pos_size / price, QTY_PREC.get(s, 2))
    
    if qty < MIN_QTY.get(s, 0.01):
        tg(m + f"❌ Q: {qty}")
        return jsonify({"e": "q"}), 400
    
    tg(m + f"💼 {s} {qty} ({pos_size} USDT)\nSL: {sl} | TP: {tp}")
    
    # Установка плеча
    bx("POST", "/openApi/swap/v2/trade/leverage", {"symbol": s, "side": "BOTH", "leverage": LEVERAGE})
    
    # Открытие позиции
    o = bx("POST", "/openApi/swap/v2/trade/order", {
        "symbol": s,
        "side": si,
        "positionSide": "BOTH",
        "type": "MARKET",
        "quantity": str(qty)
    })
    
    if o.get("code") != 0:
        tg(f"❌ Ошибка открытия: {o.get('msg')}")
        return jsonify({"e": "ord", "msg": o.get("msg")})
    
    # Установка Stop Loss
    close_side = "SELL" if si == "BUY" else "BUY"
    
    sl_order = bx("POST", "/openApi/swap/v2/trade/order", {
        "symbol": s,
        "side": close_side,
        "positionSide": "BOTH",
        "type": "STOP_MARKET",
        "stopPrice": str(sl),
        "closePosition": "true"
    })
    
    # Установка Take Profit
    tp_order = bx("POST", "/openApi/swap/v2/trade/order", {
        "symbol": s,
        "side": close_side,
        "positionSide": "BOTH",
        "type": "TAKE_PROFIT_MARKET",
        "stopPrice": str(tp),
        "closePosition": "true"
    })
    
    if sl_order.get("code") == 0 and tp_order.get("code") == 0:
        tg(f"✅ {s} {si} открыта!\n📊 SL/TP установлены")
    elif sl_order.get("code") == 0:
        tg(f"✅ {s} {si} открыта!\n⚠️ Только SL установлен")
    elif tp_order.get("code") == 0:
        tg(f"✅ {s} {si} открыта!\n⚠️ Только TP установлен")
    else:
        tg(f"✅ {s} {si} открыта!\n❌ SL/TP не установлены")
    
    return jsonify({"s": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)



