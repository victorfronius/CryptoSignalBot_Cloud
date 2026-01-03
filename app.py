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
TELEGRAM_BOT_TOKEN = "8337671886:AAFQk7A6ZYhgu63l9C2cmAj3meTJa7RD3b4"
TELEGRAM_CHAT_ID = "5411759224"

POSITION_SIZE_USDT = 7
LEVERAGE = 10
ALLOWED_TIMEFRAMES = [15]

# =============================================
# НАСТРОЙКИ BTC ФИЛЬТРА
# =============================================
BTC_FILTER_ENABLED = True
BTC_EMA_PERIOD = 20
BTC_DEVIATION_THRESHOLD = 0.5  # Порог 0.5% (было 0.3)
BTC_NEUTRAL_ALLOW_TRADING = False  # Строгий режим

# =============================================
# НАСТРОЙКИ VOLUME TRAILING STOP 🚀
# =============================================
VOLUME_TRAILING_ENABLED = True  # Включить/выключить Volume trailing
EXIT_VOLUME_THRESHOLD = 2.0     # Выход когда Volume spike падает ниже 2.0×
VOLUME_CHECK_INTERVAL = 60      # Проверка каждые 60 секунд
VOLUME_LOW_CONFIRMATIONS = 2    # Сколько раз подряд низкий Volume перед выходом

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

# Глобальный словарь для отслеживания потоков мониторинга
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
# BTC ФИЛЬТР
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
    
    ema = prices[0]
    multiplier = 2 / (period + 1)
    
    for price in prices[1:]:
        ema = (price - ema) * multiplier + ema
    
    return ema

def get_btc_trend():
    """Определяем тренд BTC"""
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
        trend = "BULLISH"
    elif deviation < -BTC_DEVIATION_THRESHOLD:
        trend = "BEARISH"
    else:
        trend = "NEUTRAL"
    
    print(f"📊 BTC: {current_price:.1f} | EMA{BTC_EMA_PERIOD}: {ema:.1f} | Dev: {deviation:.2f}% | Trend: {trend}")
    
    return trend

# =============================================
# VOLUME TRAILING STOP 🚀
# =============================================

def get_symbol_klines(symbol, interval="15m", limit=25):
    """Получить свечи для любого символа"""
    try:
        url = f"{BINGX_BASE_URL}/openApi/swap/v2/quote/klines"
        params = {
            "symbol": symbol,
            "interval": interval,
            "limit": limit
        }
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if data.get("code") == 0 and data.get("data"):
            return data["data"]
        else:
            print(f"❌ Klines error for {symbol}: {data}")
            return None
            
    except Exception as e:
        print(f"❌ Klines API error for {symbol}: {e}")
        return None

def get_current_volume_spike(symbol):
    """Получить текущий Volume spike монеты"""
    try:
        klines = get_symbol_klines(symbol, "15m", 25)
        
        if not klines or len(klines) < 21:
            return 0
        
        # Средний volume за предыдущие 20 свечей (не включая текущую)
        volumes = [float(k["volume"]) for k in klines[:-5]]
        avg_volume = sum(volumes) / len(volumes) if volumes else 1
        
        # Текущий volume (последняя закрытая свеча)
        current_volume = float(klines[-1]["volume"])
        
        # Spike множитель
        spike = current_volume / avg_volume if avg_volume > 0 else 0
        
        return spike
    except Exception as e:
        print(f"❌ Volume spike error for {symbol}: {e}")
        return 0

def is_position_open_check(symbol):
    """Проверка открыта ли позиция"""
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

def close_position_market(symbol, position_amt):
    """Закрыть позицию по рынку"""
    try:
        # Определяем направление закрытия
        side = "SELL" if position_amt > 0 else "BUY"
        qty = abs(position_amt)
        
        print(f"🚪 Закрываем {symbol}: {side} {qty}")
        
        # Закрываем позицию
        close_order = bx("POST", "/openApi/swap/v2/trade/order", {
            "symbol": symbol,
            "side": side,
            "positionSide": "BOTH",
            "type": "MARKET",
            "quantity": str(qty)
        })
        
        if close_order.get("code") == 0:
            print(f"✅ Позиция {symbol} закрыта по рынку")
            return True
        else:
            print(f"❌ Ошибка закрытия {symbol}: {close_order.get('msg')}")
            return False
            
    except Exception as e:
        print(f"❌ Exception при закрытии {symbol}: {e}")
        return False

def monitor_volume_exit(symbol):
    """Мониторинг Volume для автовыхода"""
    
    print(f"🎯 Volume мониторинг запущен для {symbol}")
    tg(f"🎯 Volume trailing активирован\n📊 {symbol}\n⚠️ Выход при Volume < {EXIT_VOLUME_THRESHOLD}×")
    
    low_volume_count = 0
    check_count = 0
    
    while True:
        try:
            time.sleep(VOLUME_CHECK_INTERVAL)
            check_count += 1
            
            # Проверяем что позиция еще открыта
            is_open, position_amt = is_position_open_check(symbol)
            
            if not is_open:
                print(f"✅ Позиция {symbol} уже закрыта, мониторинг остановлен")
                if symbol in volume_monitor_threads:
                    del volume_monitor_threads[symbol]
                break
            
            # Получаем текущий Volume spike
            current_spike = get_current_volume_spike(symbol)
            
            print(f"📊 {symbol} Volume spike: {current_spike:.2f}× (проверка #{check_count})")
            
            # Если Volume упал ниже порога
            if current_spike < EXIT_VOLUME_THRESHOLD:
                low_volume_count += 1
                print(f"⚠️ {symbol} Volume низкий ({low_volume_count}/{VOLUME_LOW_CONFIRMATIONS})")
                
                # Если достаточно подтверждений
                if low_volume_count >= VOLUME_LOW_CONFIRMATIONS:
                    print(f"🚪 {symbol} - Volume spike ушел! Закрываем позицию")
                    
                    # Закрываем позицию
                    if close_position_market(symbol, position_amt):
                        tg(f"🚪 {symbol} закрыт по Volume trailing\n💨 Volume упал: {current_spike:.1f}× < {EXIT_VOLUME_THRESHOLD}×\n📊 Киты вышли - мы тоже!")
                    
                    # Останавливаем мониторинг
                    if symbol in volume_monitor_threads:
                        del volume_monitor_threads[symbol]
                    break
            else:
                # Volume нормальный, сбрасываем счетчик
                if low_volume_count > 0:
                    print(f"✅ {symbol} Volume восстановился: {current_spike:.2f}×")
                low_volume_count = 0
                
        except Exception as e:
            print(f"❌ Ошибка в мониторинге {symbol}: {e}")
            time.sleep(30)  # Пауза при ошибке

def start_volume_monitoring(symbol):
    """Запустить мониторинг Volume в отдельном потоке"""
    
    if not VOLUME_TRAILING_ENABLED:
        print(f"⚠️ Volume trailing выключен")
        return
    
    # Если уже есть поток для этого символа, не создаем новый
    if symbol in volume_monitor_threads:
        print(f"⚠️ Мониторинг для {symbol} уже запущен")
        return
    
    # Создаем и запускаем поток
    monitor_thread = threading.Thread(
        target=monitor_volume_exit,
        args=(symbol,),
        daemon=True
    )
    monitor_thread.start()
    
    # Сохраняем ссылку на поток
    volume_monitor_threads[symbol] = monitor_thread
    
    print(f"✅ Поток мониторинга создан для {symbol}")

# =============================================

@app.route("/")
def home():
    status = "🟢 ВКЛ" if VOLUME_TRAILING_ENABLED else "🔴 ВЫКЛ"
    return f"""
    <h1>🚀 SUPER FLASK BOT</h1>
    <p>💎 7 USDT × 10x | Авто SL/TP</p>
    <p>📊 BTC Filter: {BTC_DEVIATION_THRESHOLD}%</p>
    <p>⚡ Volume Trailing: {status}</p>
    <p>🎯 Exit threshold: {EXIT_VOLUME_THRESHOLD}×</p>
    <a href='/test'>Test</a> | <a href='/btc'>BTC</a> | <a href='/status'>Status</a>
    """

@app.route("/test")
def test():
    r = bx("GET", "/openApi/swap/v2/user/balance", {})
    tg(f"🧪 Test: {r.get('code')} {r.get('msg', 'OK')}")
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
            "filter_enabled": BTC_FILTER_ENABLED,
            "threshold": BTC_DEVIATION_THRESHOLD
        })
    else:
        return jsonify({"error": "Cannot get BTC data"}), 500

@app.route("/status")
def status():
    """Статус активных мониторингов"""
    active_monitors = list(volume_monitor_threads.keys())
    return jsonify({
        "volume_trailing_enabled": VOLUME_TRAILING_ENABLED,
        "exit_threshold": EXIT_VOLUME_THRESHOLD,
        "active_monitors": active_monitors,
        "monitor_count": len(active_monitors)
    })

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
    # BTC ФИЛЬТР
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
    # ОСТАЛЬНАЯ ЛОГИКА
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
    
    # =============================================
    # ЗАПУСК VOLUME TRAILING МОНИТОРИНГА 🚀
    # =============================================
    
    # Запускаем мониторинг Volume в отдельном потоке
    start_volume_monitoring(s)
    
    # =============================================
    
    if sl_ok and tp_ok:
        tg(f"✅ {s} {si} открыта!\n📊 SL/TP установлены\n🎯 Volume trailing: активен")
    elif sl_ok:
        tg(f"✅ {s} {si} открыта!\n✅ SL установлен\n❌ TP: {tp_order.get('msg')}\n🎯 Volume trailing: активен")
    elif tp_ok:
        tg(f"✅ {s} {si} открыта!\n❌ SL: {sl_order.get('msg')}\n✅ TP установлен\n🎯 Volume trailing: активен")
    else:
        tg(f"✅ {s} {si} открыта!\n❌ SL: {sl_order.get('msg')}\n❌ TP: {tp_order.get('msg')}\n🎯 Volume trailing: активен")
    
    return jsonify({"s": "ok", "volume_trailing": VOLUME_TRAILING_ENABLED})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
