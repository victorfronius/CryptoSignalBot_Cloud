
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
    <h1>🚀 Elliott Wave Bot v9</h1>
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

    # ── EXIT сигнал — закрыть позицию и открыть обратную ──
    if dir in ("EXIT_LONG", "EXIT_SHORT"):
        if sym not in SYMBOL_MAP:
            return
        s = SYMBOL_MAP[sym]
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
                            tg(f"🚨 EXIT {s}\nРазворот на 5m — позиция закрыта\n{dir} | {abs(amt)} контрактов")
                            last_trade_time[s] = 0
                            active_positions.pop(s, None)

                            # Открываем обратную позицию
                            # EXIT_LONG = бычья свеча = разворот вверх → открываем LONG
                            # EXIT_SHORT = медвежья свеча = разворот вниз → открываем SHORT
                            new_side = "BUY" if dir == "EXIT_LONG" else "SELL"
                            time.sleep(1)
                            open_reverse_position(s, new_side)
                        else:
                            tg(f"❌ EXIT {s} ошибка: {result.get('msg')}")
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
