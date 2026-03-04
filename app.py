from flask import Flask, request, jsonify
import requests
import hmac
import hashlib
import time
import threading

app = Flask(__name__)

BINGX_API_KEY = "BMWtI97RFrKmpBEQoOvcxWA6oeL60gnWqrUqSeDNbALuBgmlyYw4KfYFfBfSqNptKN0U5jhOO4gQvOs0qiPA"
BINGX_SECRET_KEY = "qvkjbJn2yIGHaTXvfUu9a9o01UgC2S88xaDhkO2buJVdDik25ovPyzkQwCZ6O9Je6h7mKF5nBnM97YVgfvUQ"
BINGX_BASE_URL = "https://open-api.bingx.com"
TELEGRAM_BOT_TOKEN = "8003707312:AAEzu1tqQu-y3PGU6tqyDTKA0HJOfvOsu-E"
TELEGRAM_CHAT_ID = "5411759224"

POSITION_SIZE_USDT = 5
LEVERAGE = 10
ALLOWED_TIMEFRAMES = [5]

BTC_FILTER_ENABLED = False
BTC_EMA_PERIOD = 20
BTC_DEVIATION_THRESHOLD = 0.2
BTC_NEUTRAL_ALLOW_TRADING = False

VOLUME_TRAILING_ENABLED = False
EXIT_VOLUME_THRESHOLD = 0.2
VOLUME_CHECK_INTERVAL = 180
VOLUME_LOW_CONFIRMATIONS = 5
MIN_TIME_IN_POSITION = 30

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

PRICE_PREC = {
    "BTC-USDT": 1, "ETH-USDT": 2, "BNB-USDT": 2, "SOL-USDT": 2, "XRP-USDT": 4, "ADA-USDT": 4,
    "DOGE-USDT": 5, "AVAX-USDT": 2, "MATIC-USDT": 4, "DOT-USDT": 3, "TRX-USDT": 5, "LINK-USDT": 3,
    "ARB-USDT": 4, "PEPE-USDT": 10, "SHIB-USDT": 8, "FLOKI-USDT": 8, "FTM-USDT": 4, "NEAR-USDT": 3,
    "ATOM-USDT": 3, "OP-USDT": 3, "APT-USDT": 3, "IMX-USDT": 4, "LDO-USDT": 3, "WLD-USDT": 4,
    "INJ-USDT": 3, "SUI-USDT": 4,
}

volume_monitor_threads = {}

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
    p["recvWindow"] = 10000
    pay = praseParam(p)
    sig = hmac.new(BINGX_SECRET_KEY.encode(), pay.encode(), hashlib.sha256).hexdigest()
    url = f"{BINGX_BASE_URL}{e}?{pay}&signature={sig}"
    h = {"X-BX-APIKEY": BINGX_API_KEY}
    try:
        r = requests.get(url, headers=h, timeout=10) if m == "GET" else requests.post(url, headers=h, timeout=10)
        return r.json()
    except:
        return {"code": -1}

def format_price(price, symbol):
    prec = PRICE_PREC.get(symbol, 4)
    return round(float(price), prec)

def get_btc_klines():
    try:
        url = f"{BINGX_BASE_URL}/openApi/swap/v2/quote/klines"
        params = {"symbol": "BTC-USDT", "interval": "15m", "limit": 100}
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        if data.get("code") == 0 and data.get("data"):
            return [float(k["close"]) for k in data["data"]]
        return None
    except:
        return None

def calculate_ema(prices, period=20):
    if not prices or len(prices) < period:
        return None
    ema = prices[0]
    multiplier = 2 / (period + 1)
    for price in prices[1:]:
        ema = (price - ema) * multiplier + ema
    return ema

def get_btc_trend():
    if not BTC_FILTER_ENABLED:
        return "NEUTRAL"
    closes = get_btc_klines()
    if not closes:
        return None
    current_price = closes[-1]
    ema = calculate_ema(closes, BTC_EMA_PERIOD)
    if not ema:
        return None
    deviation = ((current_price - ema) / ema) * 100
    if deviation > BTC_DEVIATION_THRESHOLD:
        return "BULLISH"
    elif deviation < -BTC_DEVIATION_THRESHOLD:
        return "BEARISH"
    else:
        return "NEUTRAL"

def is_position_open_check(symbol):
    try:
        pos = bx("GET", "/openApi/swap/v2/user/positions", {})
        if pos.get("code") == 0:
            for p in pos.get("data", []):
                if p["symbol"] == symbol:
                    amt = float(p.get("positionAmt", 0))
                    if amt != 0:
                        return True, amt
        return False, 0
    except:
        return False, 0

@app.route("/")
def home():
    return """
    <h1>🚀 ELLIOTT WAVE BOT V3</h1>
    <p>💎 5 USDT × 10x</p>
    <p>✅ SL/TP с правильным swap для SHORT</p>
    <p>✅ reduceOnly для экономии маржи</p>
    """

@app.route("/webhook", methods=["POST"])
def webhook():
    d = request.json
    if not d:
        return jsonify({"error": "no json"}), 400
    
    tf = int(d.get("tf", 0))
    sym = d.get("symbol", "?")
    dir = d.get("action", "").upper()
    sig = d.get("signal", "?")
    sl_raw = d.get("sl", "na")
    tp_raw = d.get("tp1", d.get("tp", "na"))
    
    m = f"🚨 {sig}\n{sym} {dir} {tf}m\n"
    
    if tf not in ALLOWED_TIMEFRAMES:
        tg(m + "❌ TF")
        return jsonify({"s": "tf"})
    
    if sym not in SYMBOL_MAP:
        tg(m + "❌ SYM")
        return jsonify({"e": "sym"}), 400
    
    s = SYMBOL_MAP[sym]
    si = "BUY" if dir == "LONG" else "SELL"
    
    if sl_raw == "na" or tp_raw == "na":
        tg(m + "⚠️ Нет SL/TP - пропускаем")
        return jsonify({"s": "no_sltp"})
    
    try:
        sl = format_price(sl_raw, s)
        tp = format_price(tp_raw, s)
        
        # SWAP удалён - индикатор присылает правильные значения

# Минимальное расстояние TP = 1% от цены
        pr_check = bx("GET", "/openApi/swap/v2/quote/price", {"symbol": s})
        if pr_check.get("code") == 0:
            cur_price = float(pr_check["data"]["price"])
            min_dist = cur_price * 0.01
            if dir == "LONG" and (tp - cur_price) < min_dist:
                tp = format_price(cur_price * 1.01, s)
                print(f"DEBUG TP adjusted LONG: {tp}")
            elif dir == "SHORT" and (cur_price - tp) < min_dist:
                tp = format_price(cur_price * 0.99, s)
                print(f"DEBUG TP adjusted SHORT: {tp}")
            
    except:
        tg(m + "❌ Некорректные SL/TP")
        return jsonify({"e": "invalid_sltp"}), 400
    
    # Проверка существующей позиции
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
        tg(m + "❌ Цена недоступна")
        return jsonify({"e": "pr"}), 500
    
    price = float(pr["data"]["price"])
    qty = round((POSITION_SIZE_USDT * LEVERAGE) / price, QTY_PREC.get(s, 2))
    
    if qty < MIN_QTY.get(s, 0.01):
        tg(m + f"❌ Quantity слишком мал: {qty}")
        return jsonify({"e": "q"}), 400
    
    tg(m + f"💼 {s} {qty}\nSL: {sl} | TP: {tp}")
    
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
        return jsonify({"e": "ord"})
    
    # Ждем подтверждения позиции
    time.sleep(1.5)
    
    # Получаем точный quantity
    actual_qty = qty
    pos_check = bx("GET", "/openApi/swap/v2/user/positions", {})
    if pos_check.get("code") == 0:
        for p in pos_check.get("data", []):
            if p["symbol"] == s:
                actual_qty = abs(float(p.get("positionAmt", qty)))
                break
    
    close_side = "SELL" if si == "BUY" else "BUY"
    
    # SL с reduceOnly
    sl_order = bx("POST", "/openApi/swap/v2/trade/order", {
        "symbol": s,
        "side": close_side,
        "positionSide": "BOTH",
        "type": "STOP_MARKET",
        "stopPrice": str(sl),
        "quantity": str(actual_qty),
        "reduceOnly": "true",
        "workingType": "MARK_PRICE"
    })
    
    # TP с reduceOnly
    tp_order = bx("POST", "/openApi/swap/v2/trade/order", {
        "symbol": s,
        "side": close_side,
        "positionSide": "BOTH",
        "type": "TAKE_PROFIT_MARKET",
        "stopPrice": str(tp),
        "quantity": str(actual_qty),
        "reduceOnly": "true",
        "workingType": "MARK_PRICE"
    })
    
    sl_ok = sl_order.get("code") == 0
    tp_ok = tp_order.get("code") == 0
    
    price_prec = PRICE_PREC.get(s, 4)
    
    if sl_ok and tp_ok:
        tg(f"✅ {s} {si} открыта!\n📊 SL: {sl:.{price_prec}f} | TP: {tp:.{price_prec}f}\n💎 {actual_qty} × {LEVERAGE}x")
    else:
        msg_parts = [f"✅ {s} {si} открыта!"]
        if not sl_ok:
            msg_parts.append(f"❌ SL: {sl_order.get('msg')}")
        else:
            msg_parts.append(f"✅ SL: {sl:.{price_prec}f}")
        if not tp_ok:
            msg_parts.append(f"❌ TP: {tp_order.get('msg')}")
        else:
            msg_parts.append(f"✅ TP: {tp:.{price_prec}f}")
        tg("\n".join(msg_parts))
    
    return jsonify({"s": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
