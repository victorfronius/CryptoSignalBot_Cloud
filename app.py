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
ALLOWED_TIMEFRAMES = [240]

BTC_FILTER_ENABLED = False
BTC_EMA_PERIOD = 20
BTC_DEVIATION_THRESHOLD = 0.2
BTC_NEUTRAL_ALLOW_TRADING = False

VOLUME_TRAILING_ENABLED = False
EXIT_VOLUME_THRESHOLD = 0.2
VOLUME_CHECK_INTERVAL = 180
VOLUME_LOW_CONFIRMATIONS = 5
MIN_TIME_IN_POSITION = 30

# EXIT разворот — фиксированные SL/TP для новой позиции
EXIT_REVERSE_SL_PCT = 1.5   # SL = 1.5% от цены входа
EXIT_REVERSE_TP_PCT = 2.5   # TP = 2.5% от цены входа

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

last_trade_time = {}
COOLDOWN_SECONDS = 4 * 60 * 60

# Трейлинг стоп — безубыток
BREAKEVEN_ENABLED        = True
BREAKEVEN_TRIGGER_PCT    = 1.5   # при +1.5% переносим SL
BREAKEVEN_OFFSET_PCT     = 0.5   # SL = цена входа + 0.5%
BREAKEVEN_CHECK_INTERVAL = 30

# symbol -> {"entry": float, "side": "BUY"/"SELL", "be_done": bool}
active_positions = {}


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

def open_reverse_position(s, new_side):
    """Открывает обратную позицию с фиксированными SL/TP после EXIT."""
    prec = PRICE_PREC.get(s, 4)

    # Получаем текущую цену
    pr = bx("GET", "/openApi/swap/v2/quote/price", {"symbol": s})
    if pr.get("code") != 0:
        tg(f"❌ EXIT разворот {s}: цена недоступна")
        return
    price = float(pr["data"]["price"])

    qty = round((POSITION_SIZE_USDT * LEVERAGE) / price, QTY_PREC.get(s, 2))
    if qty < MIN_QTY.get(s, 0.01):
        tg(f"❌ EXIT разворот {s}: объём слишком мал")
        return

    # SL и TP фиксированные %
    if new_side == "BUY":
        sl = round(price * (1 - EXIT_REVERSE_SL_PCT / 100), prec)
        tp = round(price * (1 + EXIT_REVERSE_TP_PCT / 100), prec)
    else:
        sl = round(price * (1 + EXIT_REVERSE_SL_PCT / 100), prec)
        tp = round(price * (1 - EXIT_REVERSE_TP_PCT / 100), prec)

    # Установка плеча
    bx("POST", "/openApi/swap/v2/trade/leverage", {"symbol": s, "side": "BOTH", "leverage": LEVERAGE})

    # Открытие позиции
    o = bx("POST", "/openApi/swap/v2/trade/order", {
        "symbol": s,
        "side": new_side,
        "positionSide": "BOTH",
        "type": "MARKET",
        "quantity": str(qty)
    })

    if o.get("code") != 0:
        tg(f"❌ EXIT разворот {s}: ошибка открытия {o.get('msg')}")
        return

    last_trade_time[s] = time.time()
    active_positions[s] = {"entry": price, "side": new_side, "be_done": False}

    time.sleep(1.5)

    # Получаем точный qty
    actual_qty = qty
    pos_check = bx("GET", "/openApi/swap/v2/user/positions", {})
    if pos_check.get("code") == 0:
        for p in pos_check.get("data", []):
            if p["symbol"] == s:
                actual_qty = abs(float(p.get("positionAmt", qty)))
                break

    close_side = "SELL" if new_side == "BUY" else "BUY"

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

    dir_label = "LONG" if new_side == "BUY" else "SHORT"
    if sl_ok and tp_ok:
        tg(f"🔄 EXIT → Разворот {s} {dir_label}\n"
           f"Вход: {price:.{prec}f}\n"
           f"SL: {sl:.{prec}f} | TP: {tp:.{prec}f}\n"
           f"💎 {actual_qty} × {LEVERAGE}x")
    else:
        parts = [f"🔄 EXIT → Разворот {s} {dir_label} открыт"]
        if not sl_ok:
            parts.append(f"❌ SL: {sl_order.get('msg')}")
        else:
            parts.append(f"✅ SL: {sl:.{prec}f}")
        if not tp_ok:
            parts.append(f"❌ TP: {tp_order.get('msg')}")
        else:
            parts.append(f"✅ TP: {tp:.{prec}f}")
        tg("\n".join(parts))


def breakeven_monitor():
    """Фоновый поток — переносит SL в безубыток при +1.5%"""
    while True:
        try:
            if BREAKEVEN_ENABLED and active_positions:
                for sym, info in list(active_positions.items()):
                    if info.get("be_done"):
                        continue
                    entry = info["entry"]
                    side  = info["side"]
                    try:
                        pr = bx("GET", "/openApi/swap/v2/quote/price", {"symbol": sym})
                        if pr.get("code") != 0:
                            print(f"BE: не удалось получить цену {sym}")
                            time.sleep(5)
                            continue
                        cur_price = float(pr["data"]["price"])
                        if side == "BUY":
                            profit_pct = (cur_price - entry) / entry * 100
                        else:
                            profit_pct = (entry - cur_price) / entry * 100
                        print(f"BE мониторинг {sym}: вход={entry}, цена={cur_price}, прибыль={profit_pct:.2f}%")
                        time.sleep(1)
                        if profit_pct >= BREAKEVEN_TRIGGER_PCT:
                            if side == "BUY":
                                new_sl = round(entry * (1 + BREAKEVEN_OFFSET_PCT / 100), PRICE_PREC.get(sym, 4))
                            else:
                                new_sl = round(entry * (1 - BREAKEVEN_OFFSET_PCT / 100), PRICE_PREC.get(sym, 4))
                            orders = bx("GET", "/openApi/swap/v2/trade/openOrders", {"symbol": sym})
                            if orders.get("code") == 0:
                                for o in orders.get("data", {}).get("orders", []):
                                    if o.get("type") in ("STOP_MARKET", "STOP") and o.get("reduceOnly"):
                                        bx("DELETE", "/openApi/swap/v2/trade/order", {
                                            "symbol": sym,
                                            "orderId": o["orderId"]
                                        })
                            pos_data = bx("GET", "/openApi/swap/v2/user/positions", {})
                            actual_qty = 0
                            if pos_data.get("code") == 0:
                                for p in pos_data.get("data", []):
                                    if p["symbol"] == sym:
                                        actual_qty = abs(float(p.get("positionAmt", 0)))
                            if actual_qty > 0:
                                close_side = "SELL" if side == "BUY" else "BUY"
                                sl_result = bx("POST", "/openApi/swap/v2/trade/order", {
                                    "symbol": sym,
                                    "side": close_side,
                                    "positionSide": "BOTH",
                                    "type": "STOP_MARKET",
                                    "stopPrice": str(new_sl),
                                    "quantity": str(actual_qty),
                                    "reduceOnly": "true",
                                    "workingType": "MARK_PRICE"
                                })
                                print(f"BE SL ордер {sym}: {sl_result}")
                                if sl_result.get("code") == 0:
                                    active_positions[sym]["be_done"] = True
                                    tg(f"🔒 Безубыток {sym}\nПрибыль {profit_pct:.1f}% → SL перенесён на {new_sl}")
                                else:
                                    print(f"BE SL ошибка {sym}: {sl_result.get('msg')}")
                    except Exception as e:
                        print(f"Breakeven error {sym}: {e}")
        except Exception as e:
            print(f"Breakeven monitor error: {e}")
        time.sleep(BREAKEVEN_CHECK_INTERVAL)

threading.Thread(target=breakeven_monitor, daemon=True).start()


@app.route("/")
def home():
    return """
    <h1>🚀 Elliott Wave Bot v10</h1>
    <p>💎 5 USDT × 10x</p>
    <p>✅ SL/TP автоматически</p>
    <p>✅ Cooldown защита от двойных входов</p>
    <p>✅ Безубыток при +1.5%</p>
    <p>✅ EXIT разворот с фиксированными SL/TP</p>
    """

@app.route("/webhook", methods=["POST"])
def webhook():
    d = request.get_json(force=True, silent=True)
    if not d:
        return jsonify({"error": "no json"}), 400
    threading.Thread(target=process_signal, args=(d,)).start()
    return jsonify({"s": "ok"}), 200

def process_signal(d):

    tf = int(d.get("tf", 0))
    sym = d.get("symbol", "?")
    dir = d.get("action", "").upper()

    # ── EXIT сигнал — закрыть позицию (если есть) и открыть обратную ──
    if dir in ("EXIT_LONG", "EXIT_SHORT"):
        if sym not in SYMBOL_MAP:
            tg(f"❌ EXIT: символ {sym} не найден в SYMBOL_MAP")
            return
        s = SYMBOL_MAP[sym]
        new_side = "BUY" if dir == "EXIT_LONG" else "SELL"
        tg(f"📩 EXIT получен: {s} | {dir} | новая сторона: {new_side}")

        # Закрываем существующую позицию если есть
        pos = bx("GET", "/openApi/swap/v2/user/positions", {})
        if pos.get("code") == 0:
            for p in pos.get("data", []):
                if p["symbol"] == s:
                    amt = float(p.get("positionAmt", 0))
                    if amt != 0:
                        close_side = "SELL" if amt > 0 else "BUY"
                        result = bx("POST", "/openApi/swap/v2/trade/order", {
                            "symbol": s,
                            "side": close_side,
                            "positionSide": "BOTH",
                            "type": "MARKET",
                            "quantity": str(abs(amt)),
                            "reduceOnly": "true"
                        })
                        if result.get("code") == 0:
                            tg(f"🚨 EXIT {s}\nПозиция закрыта | {abs(amt)} контрактов")
                            last_trade_time[s] = 0
                            active_positions.pop(s, None)
                            time.sleep(1)
                        else:
                            tg(f"❌ EXIT закрытие {s}: {result.get('msg')}")

        # Открываем обратную позицию всегда
        open_reverse_position(s, new_side)
        return

    sig = d.get("signal", "?")
    sl_raw = d.get("sl", "na")
    tp_raw = d.get("tp1", d.get("tp", "na"))

    m = f"🚨 {sig}\n{sym} {dir} {tf}m\n"

    if tf not in ALLOWED_TIMEFRAMES:
        tg(m + "❌ Неверный таймфрейм")
        return

    if sym not in SYMBOL_MAP:
        tg(m + "❌ Неизвестная пара")
        return

    s = SYMBOL_MAP[sym]
    si = "BUY" if dir == "LONG" else "SELL"

    if sl_raw == "na" or tp_raw == "na":
        tg(m + "⚠️ Нет SL/TP — пропускаем")
        return

    try:
        sl = format_price(sl_raw, s)
        tp = format_price(tp_raw, s)

        print(f"DEBUG: dir={dir}, sl={sl}, tp={tp}")

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
        return

    now = time.time()
    last = last_trade_time.get(s, 0)
    if now - last < COOLDOWN_SECONDS:
        wait_min = int((COOLDOWN_SECONDS - (now - last)) / 60)
        tg(m + f"⏳ Cooldown {s}: ещё {wait_min} мин")
        return

    pos = bx("GET", "/openApi/swap/v2/user/positions", {})
    if pos.get("code") == 0:
        for p in pos.get("data", []):
            if p["symbol"] == s:
                amt = float(p.get("positionAmt", 0))
                if amt != 0:
                    tg(m + f"⚠️ Позиция уже есть: {amt}")
                    return

    pr = bx("GET", "/openApi/swap/v2/quote/price", {"symbol": s})
    if pr.get("code") != 0:
        tg(m + "❌ Цена недоступна")
        return

    price = float(pr["data"]["price"])
    qty = round((POSITION_SIZE_USDT * LEVERAGE) / price, QTY_PREC.get(s, 2))

    if qty < MIN_QTY.get(s, 0.01):
        tg(m + f"❌ Объём слишком мал: {qty}")
        return

    tg(m + f"💼 {s} {qty}\nSL: {sl} | TP: {tp}")

    bx("POST", "/openApi/swap/v2/trade/leverage", {"symbol": s, "side": "BOTH", "leverage": LEVERAGE})

    o = bx("POST", "/openApi/swap/v2/trade/order", {
        "symbol": s,
        "side": si,
        "positionSide": "BOTH",
        "type": "MARKET",
        "quantity": str(qty)
    })

    if o.get("code") != 0:
        tg(f"❌ Ошибка открытия: {o.get('msg')}")
        return

    last_trade_time[s] = time.time()
    active_positions[s] = {"entry": price, "side": si, "be_done": False}
    print(f"BE: позиция сохранена {s}, вход={price}, side={si}")

    time.sleep(1.5)

    actual_qty = qty
    pos_check = bx("GET", "/openApi/swap/v2/user/positions", {})
    if pos_check.get("code") == 0:
        for p in pos_check.get("data", []):
            if p["symbol"] == s:
                actual_qty = abs(float(p.get("positionAmt", qty)))
                break

    close_side = "SELL" if si == "BUY" else "BUY"

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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
