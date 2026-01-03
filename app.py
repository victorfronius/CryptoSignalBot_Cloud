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

POSITION_SIZE_USDT = 7
LEVERAGE = 10
ALLOWED_TIMEFRAMES = [15]

# =============================================
# НАСТРОЙКИ BTC ФИЛЬТРА
# =============================================
BTC_FILTER_ENABLED = True  # Включить/выключить фильтр
BTC_EMA_PERIOD = 20  # Период EMA для BTC
BTC_DEVIATION_THRESHOLD = 0.5  # Порог отклонения от EMA в %
BTC_NEUTRAL_ALLOW_TRADING = False  # Разрешить торговлю при боковике BTC

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

def format_price(price, symbol):
    """Форматирование цены с правильной точностью"""
    prec = PRICE_PREC.get(symbol, 4)
    return round(float(price), prec)

# =============================================
# BTC ФИЛЬТР - НОВЫЕ ФУНКЦИИ
# =============================================

def get_btc_klines():
    """Получаем свечи BTC 15m для расчета EMA"""
    try:
        url = f"{BINGX_BASE_URL}/openApi/swap/v2/quote/klines"
        params = {
            "symbol": "BTC-USDT",
            "interval": "15m",
            "limit": 100
        }
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if data.get("code") == 0 and data.get("data"):
            klines = data["data"]
            closes = [float(k["close"]) for k in klines]
            return closes
        else:
            print(f"❌ BTC klines error: {data}")
            return None
            
    except Exception as e:
        print(f"❌ BTC API error: {e}")
        return None

def calculate_ema(prices, period=20):
    """Рассчитываем EMA"""
    if not prices or len(prices) < period:
        return None
    
    # Простая EMA формула
    ema = prices[0]
    multiplier = 2 / (period + 1)
    
    for price in prices[1:]:
        ema = (price - ema) * multiplier + ema
    
    return ema

def get_btc_trend():
    """
    Определяем тренд BTC
    Возвращает: 'BULLISH', 'BEARISH', 'NEUTRAL' или None
    """
    if not BTC_FILTER_ENABLED:
        return "NEUTRAL"  # Фильтр выключен
    
    closes = get_btc_klines()
    
    if not closes:
        return None  # Ошибка получения данных
    
    current_price = closes[-1]
    ema = calculate_ema(closes, BTC_EMA_PERIOD)
    
    if not ema:
        return None
    
    # Процент отклонения от EMA
    deviation = ((current_price - ema) / ema) * 100
    
    # Определяем тренд
    if deviation > BTC_DEVIATION_THRESHOLD:
        trend = "BULLISH"
    elif deviation < -BTC_DEVIATION_THRESHOLD:
        trend = "BEARISH"
    else:
        trend = "NEUTRAL"
    
    print(f"📊 BTC: {current_price:.1f} | EMA{BTC_EMA_PERIOD}: {ema:.1f} | Dev: {deviation:.2f}% | Trend: {trend}")
    
    return trend

# =============================================

@app.route("/")
def home():
    return "<h1>🚀 BingX Bot</h1><p>7 USDT × 10x | Авто SL/TP | BTC Filter</p><a href='/test'>Test</a> | <a href='/btc'>BTC</a>"

@app.route("/test")
def test():
    r = bx("GET", "/openApi/swap/v2/user/balance", {})
    tg(f"🧪 {r.get('code')} {r.get('msg', 'OK')}")
    return jsonify(r)

@app.route("/btc")
def btc_test():
    """Тестовый endpoint для проверки BTC тренда"""
    closes = get_btc_klines()
    if closes:
        current = closes[-1]
        ema = calculate_ema(closes, BTC_EMA_PERIOD)
        deviation = ((current - ema) / ema) * 100 if ema else 0
        trend = get_btc_trend()
        
        return jsonify({
            "btc_price": round(current, 1),
            "btc_ema20": round(ema, 1) if ema else None,
            "deviation": round(deviation, 2),
            "trend": trend,
            "filter_enabled": BTC_FILTER_ENABLED
        })
    else:
        return jsonify({"error": "Cannot get BTC data"}), 500

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
    tp_raw = d.get("tp1", d.get("tp", "na"))
    
    m = f"🚨 {sig}\n{sym} {dir} {tf}m\n"
    
    # =============================================
    # BTC ФИЛЬТР - ПРОВЕРКА ТРЕНДА
    # =============================================
    if BTC_FILTER_ENABLED:
        btc_trend = get_btc_trend()
        
        if btc_trend is None:
            tg(m + "⚠️ BTC данные недоступны - пропуск")
            return jsonify({"status": "btc_error"})
        
        # Логика фильтрации
        if btc_trend == "BULLISH" and dir == "SHORT":
            tg(m + f"❌ ФИЛЬТР: SHORT против BTC ⬆️\n📊 BTC: BULLISH")
            return jsonify({"status": "filtered", "reason": "short_against_bullish_btc"})
        
        if btc_trend == "BEARISH" and dir == "LONG":
            tg(m + f"❌ ФИЛЬТР: LONG против BTC ⬇️\n📊 BTC: BEARISH")
            return jsonify({"status": "filtered", "reason": "long_against_bearish_btc"})
        
        if btc_trend == "NEUTRAL" and not BTC_NEUTRAL_ALLOW_TRADING:
            tg(m + f"⚠️ ФИЛЬТР: BTC боковик - пропуск\n📊 BTC: NEUTRAL")
            return jsonify({"status": "filtered", "reason": "btc_neutral"})
        
        # Сигнал прошел фильтр
        if btc_trend == "NEUTRAL":
            m += f"📊 BTC: боковик ✅\n"
        else:
            m += f"📊 BTC: {btc_trend} ✅\n"
    
    # =============================================
    # ОСТАЛЬНАЯ ЛОГИКА БЕЗ ИЗМЕНЕНИЙ
    # =============================================
    
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
    except:
        tg(m + "❌ Некорректные SL/TP")
        return jsonify({"e": "invalid_sltp"}), 400
    
    # Проверка позиций
    pos = bx("GET", "/openApi/swap/v2/user/positions", {})
    if pos.get("code") == 0:
        for p in pos.get("data", []):
            if p["symbol"] == s:
                amt = float(p.get("positionAmt", 0))
                if amt != 0:
                    tg(m + f"⚠️ Позиция: {amt}")
                    return jsonify({"s": "exists"})
    
    # Цена
    pr = bx("GET", "/openApi/swap/v2/quote/price", {"symbol": s})
    if pr.get("code") != 0:
        tg(m + "❌ Цена")
        return jsonify({"e": "pr"}), 500
    
    price = float(pr["data"]["price"])
    qty = round((POSITION_SIZE_USDT * LEVERAGE) / price, QTY_PREC.get(s, 2))
    
    if qty < MIN_QTY.get(s, 0.01):
        tg(m + f"❌ Q: {qty}")
        return jsonify({"e": "q"}), 400
    
    tg(m + f"💼 {s} {qty}\nSL: {sl} | TP: {tp}")
    
    # Плечо
    bx("POST", "/openApi/swap/v2/trade/leverage", {"symbol": s, "side": "BOTH", "leverage": LEVERAGE})
    
    # Открытие
    o = bx("POST", "/openApi/swap/v2/trade/order", {
        "symbol": s,
        "side": si,
        "positionSide": "BOTH",
        "type": "MARKET",
        "quantity": str(qty)
    })
    
    if o.get("code") != 0:
        tg(f"❌ {o.get('msg')}")
        return jsonify({"e": "ord"})
    
    # Небольшая пауза
    time.sleep(0.5)
    
    close_side = "SELL" if si == "BUY" else "BUY"
    
    # Stop Loss
    sl_order = bx("POST", "/openApi/swap/v2/trade/order", {
        "symbol": s,
        "side": close_side,
        "positionSide": "BOTH",
        "type": "STOP_MARKET",
        "stopPrice": str(sl),
        "closePosition": "true",
        "workingType": "MARK_PRICE"
    })
    
    # Take Profit
    tp_order = bx("POST", "/openApi/swap/v2/trade/order", {
        "symbol": s,
        "side": close_side,
        "positionSide": "BOTH",
        "type": "TAKE_PROFIT_MARKET",
        "stopPrice": str(tp),
        "closePosition": "true",
        "workingType": "MARK_PRICE"
    })
    
    sl_ok = sl_order.get("code") == 0
    tp_ok = tp_order.get("code") == 0
    
    if sl_ok and tp_ok:
        tg(f"✅ {s} {si} открыта!\n📊 SL/TP установлены")
    elif sl_ok:
        tg(f"✅ {s} {si} открыта!\n✅ SL установлен\n❌ TP: {tp_order.get('msg')}")
    elif tp_ok:
        tg(f"✅ {s} {si} открыта!\n❌ SL: {sl_order.get('msg')}\n✅ TP установлен")
    else:
        tg(f"✅ {s} {si} открыта!\n❌ SL: {sl_order.get('msg')}\n❌ TP: {tp_order.get('msg')}")
    
    return jsonify({"s": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)


