from flask import Flask, request, jsonify
import requests
import hmac
import hashlib
import time
import threading

app = Flask(__name__)

BINGX_API_KEY    = "BMWtI97RFrKmpBEQoOvcxWA6oeL60gnWqrUqSeDNbALuBgmlyYw4KfYFfBfSqNptKN0U5jhOO4gQvOs0qiPA"
BINGX_SECRET_KEY = "qvkjbJn2yIGHaTXvfUu9a9o01UgC2S88xaDhkO2buJVdDik25ovPyzkQwCZ6O9Je6h7mKF5nBnM97YVgfvUQ"
BINGX_BASE_URL   = "https://open-api.bingx.com"
TELEGRAM_BOT_TOKEN = "8003707312:AAEzu1tqQu-y3PGU6tqyDTKA0HJOfvOsu-E"
TELEGRAM_CHAT_ID   = "5411759224"

POSITION_SIZE_USDT = 5
LEVERAGE           = 10
ALLOWED_TIMEFRAMES = [240]

EXIT_REVERSE_SL_PCT = 1.5
EXIT_REVERSE_TP_PCT = 2.5

BREAKEVEN_ENABLED        = True
BREAKEVEN_TRIGGER_PCT    = 1.0
BREAKEVEN_OFFSET_PCT     = 0.5
BREAKEVEN_CHECK_INTERVAL = 30

COOLDOWN_SECONDS   = 4 * 60 * 60
LIMIT_ORDER_TTL    = 4 * 60 * 60
LIMIT_MIN_DIST_PCT = 0.1
MAX_DIST_PCT       = 8.0

RTM_TP1_PCT = 2.0
RTM_TP2_PCT = 3.5

SYMBOL_MAP = {
    "BTCUSDT":   "BTC-USDT",  "BTCUSDT.P":   "BTC-USDT",
    "ETHUSDT":   "ETH-USDT",  "ETHUSDT.P":   "ETH-USDT",
    "BNBUSDT":   "BNB-USDT",  "BNBUSDT.P":   "BNB-USDT",
    "SOLUSDT":   "SOL-USDT",  "SOLUSDT.P":   "SOL-USDT",
    "XRPUSDT":   "XRP-USDT",  "XRPUSDT.P":   "XRP-USDT",
    "ADAUSDT":   "ADA-USDT",  "ADAUSDT.P":   "ADA-USDT",
    "DOGEUSDT":  "DOGE-USDT", "DOGEUSDT.P":  "DOGE-USDT",
    "AVAXUSDT":  "AVAX-USDT", "AVAXUSDT.P":  "AVAX-USDT",
    "MATICUSDT": "MATIC-USDT","MATICUSDT.P": "MATIC-USDT",
    "DOTUSDT":   "DOT-USDT",  "DOTUSDT.P":   "DOT-USDT",
    "TRXUSDT":   "TRX-USDT",  "TRXUSDT.P":   "TRX-USDT",
    "LINKUSDT":  "LINK-USDT", "LINKUSDT.P":  "LINK-USDT",
    "ARBUSDT":   "ARB-USDT",  "ARBUSDT.P":   "ARB-USDT",
    "PEPEUSDT":  "PEPE-USDT", "PEPEUSDT.P":  "PEPE-USDT",
    "SHIBUSDT":  "SHIB-USDT", "SHIBUSDT.P":  "SHIB-USDT",
    "FLOKIUSDT": "FLOKI-USDT","FLOKIUSDT.P": "FLOKI-USDT",
    "FTMUSDT":   "FTM-USDT",  "FTMUSDT.P":   "FTM-USDT",
    "NEARUSDT":  "NEAR-USDT", "NEARUSDT.P":  "NEAR-USDT",
    "ATOMUSDT":  "ATOM-USDT", "ATOMUSDT.P":  "ATOM-USDT",
    "OPUSDT":    "OP-USDT",   "OPUSDT.P":    "OP-USDT",
    "APTUSDT":   "APT-USDT",  "APTUSDT.P":   "APT-USDT",
    "IMXUSDT":   "IMX-USDT",  "IMXUSDT.P":   "IMX-USDT",
    "LDOUSDT":   "LDO-USDT",  "LDOUSDT.P":   "LDO-USDT",
    "WLDUSDT":   "WLD-USDT",  "WLDUSDT.P":   "WLD-USDT",
    "INJUSDT":   "INJ-USDT",  "INJUSDT.P":   "INJ-USDT",
    "SUIUSDT":   "SUI-USDT",  "SUIUSDT.P":   "SUI-USDT",
}

MIN_QTY = {
    "BTC-USDT": 0.001, "ETH-USDT": 0.01,   "BNB-USDT": 0.01,
    "SOL-USDT": 0.1,   "XRP-USDT": 1,      "ADA-USDT": 1,
    "DOGE-USDT": 1,    "AVAX-USDT": 0.1,   "MATIC-USDT": 1,
    "DOT-USDT": 0.1,   "TRX-USDT": 1,      "LINK-USDT": 0.1,
    "ARB-USDT": 1,     "PEPE-USDT": 100000, "SHIB-USDT": 100000,
    "FLOKI-USDT": 10000,"FTM-USDT": 1,     "NEAR-USDT": 1,
    "ATOM-USDT": 1,    "OP-USDT": 1,        "APT-USDT": 0.1,
    "IMX-USDT": 1,     "LDO-USDT": 1,       "WLD-USDT": 1,
    "INJ-USDT": 0.1,   "SUI-USDT": 1,
}

QTY_PREC = {
    "BTC-USDT": 3,  "ETH-USDT": 2,  "BNB-USDT": 2,
    "SOL-USDT": 2,  "XRP-USDT": 0,  "ADA-USDT": 0,
    "DOGE-USDT": 0, "AVAX-USDT": 2, "MATIC-USDT": 0,
    "DOT-USDT": 2,  "TRX-USDT": 0,  "LINK-USDT": 2,
    "ARB-USDT": 0,  "PEPE-USDT": 0, "SHIB-USDT": 0,
    "FLOKI-USDT": 0,"FTM-USDT": 0,  "NEAR-USDT": 1,
    "ATOM-USDT": 1, "OP-USDT": 0,   "APT-USDT": 2,
    "IMX-USDT": 0,  "LDO-USDT": 0,  "WLD-USDT": 0,
    "INJ-USDT": 2,  "SUI-USDT": 0,
}

PRICE_PREC = {
    "BTC-USDT": 1,  "ETH-USDT": 2,  "BNB-USDT": 2,
    "SOL-USDT": 2,  "XRP-USDT": 4,  "ADA-USDT": 4,
    "DOGE-USDT": 5, "AVAX-USDT": 2, "MATIC-USDT": 4,
    "DOT-USDT": 3,  "TRX-USDT": 5,  "LINK-USDT": 3,
    "ARB-USDT": 4,  "PEPE-USDT": 10,"SHIB-USDT": 8,
    "FLOKI-USDT": 8,"FTM-USDT": 4,  "NEAR-USDT": 3,
    "ATOM-USDT": 3, "OP-USDT": 3,   "APT-USDT": 3,
    "IMX-USDT": 4,  "LDO-USDT": 3,  "WLD-USDT": 4,
    "INJ-USDT": 3,  "SUI-USDT": 4,
}

last_trade_time     = {}
active_positions    = {}
active_limit_orders = {}

# ──────────────────────────────────────────────────────────────
# УТИЛИТЫ
# ──────────────────────────────────────────────────────────────

def tg(msg):
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        try:
            requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                data={"chat_id": TELEGRAM_CHAT_ID, "text": msg},
                timeout=5
            )
        except:
            pass


def praseParam(p):
    s = sorted(p)
    return "&".join([f"{x}={p[x]}" for x in s]) + "&timestamp=" + str(p["timestamp"])


def bx(method, endpoint, params=None):
    if not params:
        params = {}
    params["timestamp"] = int(time.time() * 1000)
    params["recvWindow"] = 10000
    payload = praseParam(params)
    sig = hmac.new(BINGX_SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()
    url = f"{BINGX_BASE_URL}{endpoint}?{payload}&signature={sig}"
    headers = {"X-BX-APIKEY": BINGX_API_KEY}
    try:
        if method == "GET":
            r = requests.get(url, headers=headers, timeout=10)
        elif method == "DELETE":
            r = requests.delete(url, headers=headers, timeout=10)
        else:
            r = requests.post(url, headers=headers, timeout=10)
        return r.json()
    except:
        return {"code": -1}


def format_price(price, symbol):
    return round(float(price), PRICE_PREC.get(symbol, 4))


def get_current_price(symbol):
    pr = bx("GET", "/openApi/swap/v2/quote/price", {"symbol": symbol})
    if pr.get("code") == 0:
        return float(pr["data"]["price"])
    return None


# ──────────────────────────────────────────────────────────────
# LIMIT ОРДЕР
# ──────────────────────────────────────────────────────────────

def place_limit_order(s, si, limit_price, sl, tp1, tp2, signal_name, zone_hi=None, zone_lo=None):
    prec = PRICE_PREC.get(s, 4)

    cur_price = get_current_price(s)
    if cur_price is None:
        tg(f"❌ LIMIT {s}: текущая цена недоступна")
        return

    # Проверка дистанции
    if si == "BUY":
        dist = (cur_price - limit_price) / cur_price * 100
        if dist < LIMIT_MIN_DIST_PCT:
            tg(f"⚠️ LIMIT LONG {s}: слишком близко ({dist:.1f}%) — пропускаем")
            return
        if dist > MAX_DIST_PCT:
            tg(f"⚠️ LIMIT LONG {s}: слишком далеко ({dist:.1f}%) — пропускаем")
            return
    else:
        dist = (limit_price - cur_price) / cur_price * 100
        if dist < LIMIT_MIN_DIST_PCT:
            tg(f"⚠️ LIMIT SHORT {s}: слишком близко ({dist:.1f}%) — пропускаем")
            return
        if dist > MAX_DIST_PCT:
            tg(f"⚠️ LIMIT SHORT {s}: слишком далеко ({dist:.1f}%) — пропускаем")
            return

    # Cooldown
    now = time.time()
    if now - last_trade_time.get(s, 0) < COOLDOWN_SECONDS:
        wait_min = int((COOLDOWN_SECONDS - (now - last_trade_time[s])) / 60)
        tg(f"⏳ LIMIT cooldown {s}: ещё {wait_min} мин")
        return

    # Проверка открытой позиции
    pos = bx("GET", "/openApi/swap/v2/user/positions", {})
    if pos.get("code") == 0:
        for p in pos.get("data", []):
            if p["symbol"] == s and abs(float(p.get("positionAmt", 0))) > 0:
                tg(f"⚠️ LIMIT {s}: позиция уже открыта")
                return

    # Отмена старого лимита
    if s in active_limit_orders:
        old_order = active_limit_orders[s]
        cancel = bx("DELETE", "/openApi/swap/v2/trade/order",
                    {"symbol": s, "orderId": old_order["order_id"]})
        if cancel.get("code") == 0:
            tg(f"🔄 LIMIT {s}: старый ордер #{old_order['order_id']} отменён")
        active_limit_orders.pop(s, None)

    # Объём
    qty = round((POSITION_SIZE_USDT * LEVERAGE) / limit_price, QTY_PREC.get(s, 2))
    if qty < MIN_QTY.get(s, 0.01):
        tg(f"❌ LIMIT {s}: объём {qty} меньше минимума")
        return

    # Плечо
    bx("POST", "/openApi/swap/v2/trade/leverage",
       {"symbol": s, "side": "BOTH", "leverage": LEVERAGE})

    # Выставляем ордер
    o = bx("POST", "/openApi/swap/v2/trade/order", {
        "symbol":       s,
        "side":         si,
        "positionSide": "BOTH",
        "type":         "LIMIT",
        "price":        str(limit_price),
        "quantity":     str(qty),
        "timeInForce":  "GTC"
    })

    print(f"LIMIT ORDER RESPONSE {s}: {o}")

    if o.get("code") != 0:
        tg(f"❌ LIMIT {s} {si}: ошибка — {o.get('msg')} | code={o.get('code')}")
        return

    order_id = str(o.get("data", {}).get("orderId", "?"))

    active_limit_orders[s] = {
        "order_id":    order_id,
        "side":        si,
        "qty":         qty,
        "limit_price": limit_price,
        "sl":          sl,
        "tp1":         tp1,
        "tp2":         tp2,
        "signal":      signal_name,
        "placed_at":   time.time()
    }

    dir_label = "LONG" if si == "BUY" else "SHORT"
    zone_str  = f"Зона: {zone_lo:.{prec}f} – {zone_hi:.{prec}f}\n" if zone_hi and zone_lo else ""
    tg(
        f"📋 LIMIT {dir_label} выставлен\n"
        f"Symbol: {s}\n"
        f"Signal: {signal_name}\n"
        f"Лимит: {limit_price:.{prec}f} | Текущая: {cur_price:.{prec}f}\n"
        f"{zone_str}"
        f"SL: {sl:.{prec}f}\n"
        f"TP1: {tp1:.{prec}f} | TP2: {tp2:.{prec}f}\n"
        f"Объём: {qty} × {LEVERAGE}x\n"
        f"ID: #{order_id}"
    )


def attach_sl_tp_to_filled_limit(s):
    info = active_limit_orders.get(s)
    if not info:
        return

    si    = info["side"]
    sl    = info["sl"]
    tp1   = info["tp1"]
    entry = info["limit_price"]
    prec  = PRICE_PREC.get(s, 4)

    actual_qty = info["qty"]
    pos_data = bx("GET", "/openApi/swap/v2/user/positions", {})
    if pos_data.get("code") == 0:
        for p in pos_data.get("data", []):
            if p["symbol"] == s:
                actual_qty = abs(float(p.get("positionAmt", info["qty"])))
                break

    close_side = "SELL" if si == "BUY" else "BUY"

    sl_order = bx("POST", "/openApi/swap/v2/trade/order", {
        "symbol":       s,
        "side":         close_side,
        "positionSide": "BOTH",
        "type":         "STOP_MARKET",
        "stopPrice":    str(sl),
        "quantity":     str(actual_qty),
        "reduceOnly":   "true",
        "workingType":  "MARK_PRICE"
    })

    tp_order = bx("POST", "/openApi/swap/v2/trade/order", {
        "symbol":       s,
        "side":         close_side,
        "positionSide": "BOTH",
        "type":         "TAKE_PROFIT_MARKET",
        "stopPrice":    str(tp1),
        "quantity":     str(actual_qty),
        "reduceOnly":   "true",
        "workingType":  "MARK_PRICE"
    })

    sl_ok = sl_order.get("code") == 0
    tp_ok = tp_order.get("code") == 0

    last_trade_time[s]  = time.time()
    active_positions[s] = {"entry": entry, "side": si, "be_done": False}
    active_limit_orders.pop(s, None)

    dir_label = "LONG" if si == "BUY" else "SHORT"
    if sl_ok and tp_ok:
        tg(f"✅ LIMIT исполнен → {s} {dir_label}\nВход: {entry:.{prec}f}\nSL: {sl:.{prec}f} | TP: {tp1:.{prec}f}\nОбъём: {actual_qty} × {LEVERAGE}x")
    else:
        parts = [f"✅ LIMIT исполнен → {s} {dir_label}"]
        parts.append(f"{'✅' if sl_ok else '❌'} SL: {sl:.{prec}f}")
        parts.append(f"{'✅' if tp_ok else '❌'} TP: {tp1:.{prec}f}")
        tg("\n".join(parts))


# ──────────────────────────────────────────────────────────────
# МОНИТОРИНГ ЛИМИТНЫХ ОРДЕРОВ
# ──────────────────────────────────────────────────────────────

def limit_order_monitor():
    while True:
        try:
            for s, info in list(active_limit_orders.items()):
                try:
                    age = time.time() - info["placed_at"]
                    if age > LIMIT_ORDER_TTL:
                        cancel = bx("DELETE", "/openApi/swap/v2/trade/order",
                                    {"symbol": s, "orderId": info["order_id"]})
                        prec = PRICE_PREC.get(s, 4)
                        if cancel.get("code") == 0:
                            tg(f"⏰ LIMIT {s} #{info['order_id']} истёк TTL → отменён")
                        active_limit_orders.pop(s, None)
                        continue

                    order_status = bx("GET", "/openApi/swap/v2/trade/order",
                                      {"symbol": s, "orderId": info["order_id"]})
                    if order_status.get("code") != 0:
                        continue

                    status = order_status.get("data", {}).get("order", {}).get("status", "")

                    if status == "FILLED":
                        print(f"LIMIT FILLED: {s} #{info['order_id']}")
                        attach_sl_tp_to_filled_limit(s)
                    elif status in ("CANCELLED", "EXPIRED", "REJECTED"):
                        tg(f"❌ LIMIT {s} #{info['order_id']} статус: {status}")
                        active_limit_orders.pop(s, None)

                except Exception as e:
                    print(f"limit_order_monitor inner error {s}: {e}")

        except Exception as e:
            print(f"limit_order_monitor error: {e}")

        time.sleep(60)


threading.Thread(target=limit_order_monitor, daemon=True).start()


# ──────────────────────────────────────────────────────────────
# БЕЗУБЫТОК
# ──────────────────────────────────────────────────────────────

def breakeven_monitor():
    while True:
        try:
            if BREAKEVEN_ENABLED and active_positions:
                for sym, info in list(active_positions.items()):
                    if info.get("be_done"):
                        continue
                    entry = info["entry"]
                    side  = info["side"]
                    try:
                        cur_price = get_current_price(sym)
                        if cur_price is None:
                            continue

                        profit_pct = ((cur_price - entry) / entry * 100) if side == "BUY" \
                                     else ((entry - cur_price) / entry * 100)

                        if profit_pct >= BREAKEVEN_TRIGGER_PCT:
                            prec   = PRICE_PREC.get(sym, 4)
                            new_sl = round(entry * (1 + BREAKEVEN_OFFSET_PCT / 100), prec) if side == "BUY" \
                                     else round(entry * (1 - BREAKEVEN_OFFSET_PCT / 100), prec)

                            orders = bx("GET", "/openApi/swap/v2/trade/openOrders", {"symbol": sym})
                            if orders.get("code") == 0:
                                for o in orders.get("data", {}).get("orders", []):
                                    if o.get("type") in ("STOP_MARKET", "STOP") and o.get("reduceOnly"):
                                        bx("DELETE", "/openApi/swap/v2/trade/order",
                                           {"symbol": sym, "orderId": o["orderId"]})

                            pos_data   = bx("GET", "/openApi/swap/v2/user/positions", {})
                            actual_qty = 0
                            if pos_data.get("code") == 0:
                                for p in pos_data.get("data", []):
                                    if p["symbol"] == sym:
                                        actual_qty = abs(float(p.get("positionAmt", 0)))

                            if actual_qty > 0:
                                close_side = "SELL" if side == "BUY" else "BUY"
                                sl_result  = bx("POST", "/openApi/swap/v2/trade/order", {
                                    "symbol":       sym,
                                    "side":         close_side,
                                    "positionSide": "BOTH",
                                    "type":         "STOP_MARKET",
                                    "stopPrice":    str(new_sl),
                                    "quantity":     str(actual_qty),
                                    "reduceOnly":   "true",
                                    "workingType":  "MARK_PRICE"
                                })
                                if sl_result.get("code") == 0:
                                    active_positions[sym]["be_done"] = True
                                    tg(f"🔒 Безубыток {sym}\nP={profit_pct:.1f}% → SL на {new_sl:.{prec}f}")
                                else:
                                    print(f"BE SL ошибка {sym}: {sl_result.get('msg')}")

                    except Exception as e:
                        print(f"BE error {sym}: {e}")

        except Exception as e:
            print(f"BE monitor error: {e}")

        time.sleep(BREAKEVEN_CHECK_INTERVAL)


threading.Thread(target=breakeven_monitor, daemon=True).start()


# ──────────────────────────────────────────────────────────────
# EXIT РАЗВОРОТ
# ──────────────────────────────────────────────────────────────

def open_reverse_position(s, new_side):
    prec  = PRICE_PREC.get(s, 4)
    price = get_current_price(s)
    if price is None:
        tg(f"❌ EXIT разворот {s}: цена недоступна")
        return

    qty = round((POSITION_SIZE_USDT * LEVERAGE) / price, QTY_PREC.get(s, 2))
    if qty < MIN_QTY.get(s, 0.01):
        tg(f"❌ EXIT разворот {s}: объём {qty} слишком мал")
        return

    sl = round(price * (1 - EXIT_REVERSE_SL_PCT / 100), prec) if new_side == "BUY" \
         else round(price * (1 + EXIT_REVERSE_SL_PCT / 100), prec)
    tp = round(price * (1 + EXIT_REVERSE_TP_PCT / 100), prec) if new_side == "BUY" \
         else round(price * (1 - EXIT_REVERSE_TP_PCT / 100), prec)

    bx("POST", "/openApi/swap/v2/trade/leverage",
       {"symbol": s, "side": "BOTH", "leverage": LEVERAGE})

    o = bx("POST", "/openApi/swap/v2/trade/order", {
        "symbol":       s,
        "side":         new_side,
        "positionSide": "BOTH",
        "type":         "MARKET",
        "quantity":     str(qty)
    })

    if o.get("code") != 0:
        tg(f"❌ EXIT разворот {s}: {o.get('msg')}")
        return

    last_trade_time[s]  = time.time()
    active_positions[s] = {"entry": price, "side": new_side, "be_done": False}
    time.sleep(1.5)

    actual_qty = qty
    pos_check  = bx("GET", "/openApi/swap/v2/user/positions", {})
    if pos_check.get("code") == 0:
        for p in pos_check.get("data", []):
            if p["symbol"] == s:
                actual_qty = abs(float(p.get("positionAmt", qty)))
                break

    close_side = "SELL" if new_side == "BUY" else "BUY"
    sl_order   = bx("POST", "/openApi/swap/v2/trade/order", {
        "symbol": s, "side": close_side, "positionSide": "BOTH",
        "type": "STOP_MARKET", "stopPrice": str(sl),
        "quantity": str(actual_qty), "reduceOnly": "true", "workingType": "MARK_PRICE"
    })
    tp_order   = bx("POST", "/openApi/swap/v2/trade/order", {
        "symbol": s, "side": close_side, "positionSide": "BOTH",
        "type": "TAKE_PROFIT_MARKET", "stopPrice": str(tp),
        "quantity": str(actual_qty), "reduceOnly": "true", "workingType": "MARK_PRICE"
    })

    dir_label = "LONG" if new_side == "BUY" else "SHORT"
    sl_ok     = sl_order.get("code") == 0
    tp_ok     = tp_order.get("code") == 0

    if sl_ok and tp_ok:
        tg(f"🔄 EXIT → {s} {dir_label}\nВход: {price:.{prec}f}\nSL: {sl:.{prec}f} | TP: {tp:.{prec}f}\n💎 {actual_qty} × {LEVERAGE}x")
    else:
        parts = [f"🔄 EXIT → {s} {dir_label} открыт"]
        parts.append(f"{'✅' if sl_ok else '❌'} SL: {sl:.{prec}f}")
        parts.append(f"{'✅' if tp_ok else '❌'} TP: {tp:.{prec}f}")
        tg("\n".join(parts))


# ──────────────────────────────────────────────────────────────
# WEBHOOK
# ──────────────────────────────────────────────────────────────

@app.route("/")
def home():
    return """
    <h1>🚀 Elliott Wave Bot v14</h1>
    <p>💎 5 USDT × 10x</p>
    <p>✅ MARKET: W3/W5 сигналы</p>
    <p>✅ LIMIT: W2/W4/RTM зоны</p>
    <p>✅ Безубыток при +1.0%</p>
    <p>✅ EXIT разворот</p>
    <p>✅ Cooldown 4H</p>
    <p>✅ Debug лог ордеров</p>
    """


@app.route("/webhook", methods=["POST"])
def webhook():
    d = request.get_json(force=True, silent=True)
    if not d:
        return jsonify({"error": "no json"}), 400
    threading.Thread(target=process_signal, args=(d,)).start()
    return jsonify({"s": "ok"}), 200


def process_signal(d):
    tf     = int(d.get("tf", 0))
    sym    = d.get("symbol", "?")
    action = d.get("action", "").upper()
    signal = d.get("signal", "?")
    order_type = d.get("order_type", "MARKET").upper()

    # ── EXIT ──
    if action in ("EXIT_LONG", "EXIT_SHORT"):
        if sym not in SYMBOL_MAP:
            tg(f"❌ EXIT: символ {sym} не в SYMBOL_MAP")
            return
        s        = SYMBOL_MAP[sym]
        new_side = "BUY" if action == "EXIT_LONG" else "SELL"
        tg(f"📩 EXIT: {s} | {action}")

        pos = bx("GET", "/openApi/swap/v2/user/positions", {})
        if pos.get("code") == 0:
            for p in pos.get("data", []):
                if p["symbol"] == s:
                    amt = float(p.get("positionAmt", 0))
                    if amt != 0:
                        close_side = "SELL" if amt > 0 else "BUY"
                        result     = bx("POST", "/openApi/swap/v2/trade/order", {
                            "symbol": s, "side": close_side,
                            "positionSide": "BOTH", "type": "MARKET",
                            "quantity": str(abs(amt)), "reduceOnly": "true"
                        })
                        if result.get("code") == 0:
                            tg(f"🚨 EXIT {s}: закрыта {abs(amt)} контрактов")
                            last_trade_time[s] = 0
                            active_positions.pop(s, None)
                            time.sleep(1)
                        else:
                            tg(f"❌ EXIT закрытие {s}: {result.get('msg')}")
        open_reverse_position(s, new_side)
        return

    # ── Базовые проверки ──
    m = f"🚨 {signal}\n{sym} {action} {tf}m\n"

    if tf not in ALLOWED_TIMEFRAMES:
        tg(m + "❌ Неверный таймфрейм")
        return
    if sym not in SYMBOL_MAP:
        tg(m + "❌ Неизвестная пара")
        return

    s  = SYMBOL_MAP[sym]
    si = "BUY" if action == "LONG" else "SELL"

    # ── LIMIT ОРДЕР ──
    if order_type == "LIMIT":
        try:
            limit_price = format_price(
                d.get("limit_price", d.get("zone_lo") if si == "BUY" else d.get("zone_hi")), s)
            sl = format_price(d["sl"], s)
            zone_hi = float(d["zone_hi"]) if "zone_hi" in d else None
            zone_lo = float(d["zone_lo"]) if "zone_lo" in d else None

            raw_tp1 = d.get("tp1", 0)
            raw_tp2 = d.get("tp2", 0)

            if raw_tp1:
                tp1 = format_price(raw_tp1, s)
                tp2 = format_price(raw_tp2 if raw_tp2 else raw_tp1, s)
            else:
                # RTM — нет tp1, считаем по %
                if si == "BUY":
                    tp1 = format_price(limit_price * (1 + RTM_TP1_PCT / 100), s)
                    tp2 = format_price(limit_price * (1 + RTM_TP2_PCT / 100), s)
                else:
                    tp1 = format_price(limit_price * (1 - RTM_TP1_PCT / 100), s)
                    tp2 = format_price(limit_price * (1 - RTM_TP2_PCT / 100), s)

        except (KeyError, TypeError, ValueError) as e:
            tg(m + f"❌ LIMIT: некорректные параметры — {e}")
            return

        place_limit_order(s, si, limit_price, sl, tp1, tp2, signal, zone_hi, zone_lo)
        return

    # ── MARKET ОРДЕР ──
    sl_raw = d.get("sl", "na")
    tp_raw = d.get("tp1", d.get("tp", "na"))

    if sl_raw == "na" or tp_raw == "na":
        tg(m + "⚠️ Нет SL/TP — пропускаем")
        return

    try:
        sl = format_price(sl_raw, s)
        tp = format_price(tp_raw, s)

        pr_check = bx("GET", "/openApi/swap/v2/quote/price", {"symbol": s})
        if pr_check.get("code") == 0:
            cur_price = float(pr_check["data"]["price"])
            min_dist  = cur_price * 0.01
            if action == "LONG" and (tp - cur_price) < min_dist:
                tp = format_price(cur_price * 1.01, s)
            elif action == "SHORT" and (cur_price - tp) < min_dist:
                tp = format_price(cur_price * 0.99, s)
    except:
        tg(m + "❌ Некорректные SL/TP")
        return

    now  = time.time()
    last = last_trade_time.get(s, 0)
    if now - last < COOLDOWN_SECONDS:
        wait_min = int((COOLDOWN_SECONDS - (now - last)) / 60)
        tg(m + f"⏳ Cooldown {s}: ещё {wait_min} мин")
        return

    pos = bx("GET", "/openApi/swap/v2/user/positions", {})
    if pos.get("code") == 0:
        for p in pos.get("data", []):
            if p["symbol"] == s and abs(float(p.get("positionAmt", 0))) > 0:
                tg(m + "⚠️ Позиция уже есть")
                return

    price = get_current_price(s)
    if price is None:
        tg(m + "❌ Цена недоступна")
        return

    qty = round((POSITION_SIZE_USDT * LEVERAGE) / price, QTY_PREC.get(s, 2))
    if qty < MIN_QTY.get(s, 0.01):
        tg(m + f"❌ Объём слишком мал: {qty}")
        return

    tg(m + f"💼 {s} {qty}\nSL: {sl} | TP: {tp}")

    bx("POST", "/openApi/swap/v2/trade/leverage",
       {"symbol": s, "side": "BOTH", "leverage": LEVERAGE})

    o = bx("POST", "/openApi/swap/v2/trade/order", {
        "symbol":       s,
        "side":         si,
        "positionSide": "BOTH",
        "type":         "MARKET",
        "quantity":     str(qty)
    })

    if o.get("code") != 0:
        tg(f"❌ Ошибка открытия: {o.get('msg')}")
        return

    last_trade_time[s]  = time.time()
    active_positions[s] = {"entry": price, "side": si, "be_done": False}
    time.sleep(1.5)

    actual_qty = qty
    pos_check  = bx("GET", "/openApi/swap/v2/user/positions", {})
    if pos_check.get("code") == 0:
        for p in pos_check.get("data", []):
            if p["symbol"] == s:
                actual_qty = abs(float(p.get("positionAmt", qty)))
                break

    close_side = "SELL" if si == "BUY" else "BUY"
    prec       = PRICE_PREC.get(s, 4)

    sl_order = bx("POST", "/openApi/swap/v2/trade/order", {
        "symbol": s, "side": close_side, "positionSide": "BOTH",
        "type": "STOP_MARKET", "stopPrice": str(sl),
        "quantity": str(actual_qty), "reduceOnly": "true", "workingType": "MARK_PRICE"
    })
    tp_order = bx("POST", "/openApi/swap/v2/trade/order", {
        "symbol": s, "side": close_side, "positionSide": "BOTH",
        "type": "TAKE_PROFIT_MARKET", "stopPrice": str(tp),
        "quantity": str(actual_qty), "reduceOnly": "true", "workingType": "MARK_PRICE"
    })

    sl_ok = sl_order.get("code") == 0
    tp_ok = tp_order.get("code") == 0

    if sl_ok and tp_ok:
        tg(f"✅ {s} {si} открыта!\nSL: {sl:.{prec}f} | TP: {tp:.{prec}f}\n💎 {actual_qty} × {LEVERAGE}x")
    else:
        parts = [f"✅ {s} {si} открыта!"]
        parts.append(f"{'✅' if sl_ok else '❌'} SL: {sl:.{prec}f}")
        parts.append(f"{'✅' if tp_ok else '❌'} TP: {tp:.{prec}f}")
        tg("\n".join(parts))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
