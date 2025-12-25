from flask import Flask, request
import requests
import hmac
import hashlib
import time
import os
from datetime import datetime

app = Flask(__name__)

# ==========================
#  TELEGRAM
# ==========================
BOT_TOKEN = os.getenv("BOT_TOKEN", "8337671886:AAFQk7A6ZYhgu63l9C2cmAj3meTJa7RD3b4")
CHAT_ID = os.getenv("CHAT_ID", "5411759224")

# ==========================
#  BINGX API
# ==========================
BINGX_API_KEY = os.getenv("BINGX_API_KEY", "tfi2cWlGNK9eSpDJlxNks2w7DBiT6lTlUiXLjkBQhe7sIgVv7HKWiByVhDSagmrZBSgb8Hoaog1N4HzYffQ")
BINGX_SECRET_KEY = os.getenv("BINGX_SECRET_KEY", "SnNoEvoc1ZBhwHYMzi1KfAIvvgnI8eWs6b4fyjo9i7u0pcsHijJ7YIEngeHUVD19YxLeyrp2yE9UPjYAqM65w")

BINGX_BASE_URL = "https://open-api.bingx.com"

# ==========================
#  НАСТРОЙКИ ТОРГОВЛИ
# ==========================
ENABLE_TRADING = True
POSITION_SIZE_USDT = 5
LEVERAGE = 10
USE_MARKET_ORDER = True

# ==========================
#  СООТВЕТСТВИЕ СИМВОЛОВ
# ==========================
SYMBOL_MAP = {
    # Основные монеты
    "BTCUSDT": "BTC-USDT",
    "ETHUSDT": "ETH-USDT",
    "BNBUSDT": "BNB-USDT",
    "SOLUSDT": "SOL-USDT",
    "XRPUSDT": "XRP-USDT",
    "ADAUSDT": "ADA-USDT",
    "DOGEUSDT": "DOGE-USDT",
    "AVAXUSDT": "AVAX-USDT",
    "MATICUSDT": "MATIC-USDT",
    "DOTUSDT": "DOT-USDT",
    "TRXUSDT": "TRX-USDT",
    "LINKUSDT": "LINK-USDT",
    "ARBUSDT": "ARB-USDT",
    
    # Новые монеты
    "PEPEUSDT": "PEPE-USDT",
    "SHIBUSDT": "SHIB-USDT",
    "FLOKIUSDT": "FLOKI-USDT",
    "FTMUSDT": "FTM-USDT",
    "NEARUSDT": "NEAR-USDT",
    "ATOMUSDT": "ATOM-USDT",
    "OPUSDT": "OP-USDT",
    "APTUSDT": "APT-USDT",
    "IMXUSDT": "IMX-USDT",
    "LDOUSDT": "LDO-USDT",
    "WLDUSDT": "WLD-USDT",
    "INJUSDT": "INJ-USDT",
    
    # С суффиксом .P (Perpetual)
    "BTCUSDT.P": "BTC-USDT",
    "ETHUSDT.P": "ETH-USDT",
    "BNBUSDT.P": "BNB-USDT",
    "SOLUSDT.P": "SOL-USDT",
    "XRPUSDT.P": "XRP-USDT",
    "ADAUSDT.P": "ADA-USDT",
    "DOGEUSDT.P": "DOGE-USDT",
    "AVAXUSDT.P": "AVAX-USDT",
    "MATICUSDT.P": "MATIC-USDT",
    "DOTUSDT.P": "DOT-USDT",
    "TRXUSDT.P": "TRX-USDT",
    "LINKUSDT.P": "LINK-USDT",
    "ARBUSDT.P": "ARB-USDT",
    "PEPEUSDT.P": "PEPE-USDT",
    "SHIBUSDT.P": "SHIB-USDT",
    "FLOKIUSDT.P": "FLOKI-USDT",
    "FTMUSDT.P": "FTM-USDT",
    "NEARUSDT.P": "NEAR-USDT",
    "ATOMUSDT.P": "ATOM-USDT",
    "OPUSDT.P": "OP-USDT",
    "APTUSDT.P": "APT-USDT",
    "IMXUSDT.P": "IMX-USDT",
    "LDOUSDT.P": "LDO-USDT",
    "WLDUSDT.P": "WLD-USDT",
    "INJUSDT.P": "INJ-USDT",
}

# Precision для разных символов (количество знаков после запятой)
QUANTITY_PRECISION = {
    # Основные
    "BTC-USDT": 3,
    "ETH-USDT": 2,
    "BNB-USDT": 2,
    "SOL-USDT": 2,
    "XRP-USDT": 0,
    "ADA-USDT": 0,
    "DOGE-USDT": 0,
    "AVAX-USDT": 2,
    "MATIC-USDT": 0,
    "DOT-USDT": 2,
    "TRX-USDT": 0,
    "LINK-USDT": 2,
    "ARB-USDT": 0,
    
    # Новые монеты
    "PEPE-USDT": 0,      # очень дешевая
    "SHIB-USDT": 0,      # очень дешевая
    "FLOKI-USDT": 0,     # очень дешевая
    "FTM-USDT": 0,       # ~$1
    "NEAR-USDT": 1,      # ~$5
    "ATOM-USDT": 1,      # ~$6.5
    "OP-USDT": 0,        # ~$1.8
    "APT-USDT": 2,       # ~$9
    "IMX-USDT": 0,       # ~$1.5
    "LDO-USDT": 0,       # ~$1.8
    "WLD-USDT": 0,       # ~$2
    "INJ-USDT": 2,       # ~$22
}

# Минимальные объёмы для BingX
MIN_QUANTITY = {
    # Основные
    "BTC-USDT": 0.001,
    "ETH-USDT": 0.01,
    "BNB-USDT": 0.01,
    "SOL-USDT": 0.1,
    "XRP-USDT": 1,
    "ADA-USDT": 1,
    "DOGE-USDT": 1,
    "AVAX-USDT": 0.1,
    "MATIC-USDT": 1,
    "DOT-USDT": 0.1,
    "TRX-USDT": 1,
    "LINK-USDT": 0.1,
    "ARB-USDT": 1,
    
    # Новые монеты (примерные значения)
    "PEPE-USDT": 100000,     # очень дешевая мем-монета
    "SHIB-USDT": 100000,     # очень дешевая мем-монета
    "FLOKI-USDT": 10000,     # дешевая мем-монета
    "FTM-USDT": 1,           # ~$1
    "NEAR-USDT": 1,          # ~$5
    "ATOM-USDT": 1,          # ~$6.5
    "OP-USDT": 1,            # ~$1.8
    "APT-USDT": 0.1,         # ~$9
    "IMX-USDT": 1,           # ~$1.5
    "LDO-USDT": 1,           # ~$1.8
    "WLD-USDT": 1,           # ~$2
    "INJ-USDT": 0.1,         # ~$22
}

# ==========================
#  ФУНКЦИИ BINGX
# ==========================
def create_signature(params: dict, secret_key: str) -> str:
    query_string = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
    return hmac.new(
        secret_key.encode("utf-8"),
        query_string.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def bingx_request(method: str, endpoint: str, params: dict | None = None) -> dict:
    if params is None:
        params = {}

    params["timestamp"] = int(time.time() * 1000)
    
    if method == "POST":
        params["recvWindow"] = 5000
    
    signature = create_signature(params, BINGX_SECRET_KEY)
    params["signature"] = signature

    headers = {
        "X-BX-APIKEY": BINGX_API_KEY,
        "Content-Type": "application/x-www-form-urlencoded",
    }

    url = f"{BINGX_BASE_URL}{endpoint}"

    try:
        if method == "GET":
            r = requests.get(url, params=params, headers=headers, timeout=10)
        elif method == "POST":
            r = requests.post(url, params=params, headers=headers, timeout=10)
        else:
            r = requests.request(method, url, params=params, headers=headers, timeout=10)

        response = r.json()
        print(f"BingX response: {response}")
        return response
    except Exception as e:
        print(f"BingX error: {e}")
        return {"code": -1, "msg": str(e)}


def get_account_balance():
    endpoint = "/openApi/swap/v2/user/balance"
    return bingx_request("GET", endpoint)


def get_open_positions():
    endpoint = "/openApi/swap/v2/user/positions"
    return bingx_request("GET", endpoint)


def has_open_position(symbol: str, side: str) -> bool:
    positions = get_open_positions()
    
    if positions.get("code") != 0:
        return False
    
    data = positions.get("data", [])
    
    for pos in data:
        if pos.get("symbol") == symbol:
            position_amt = float(pos.get("positionAmt", 0))
            
            if side == "BUY" and position_amt > 0:
                return True
            if side == "SELL" and position_amt < 0:
                return True
    
    return False


def set_leverage(symbol: str, leverage: int):
    endpoint = "/openApi/swap/v2/trade/leverage"
    params = {
        "symbol": symbol,
        "side": "BOTH",
        "leverage": leverage,
    }
    return bingx_request("POST", endpoint, params)


def calculate_quantity(symbol: str, usdt_amount: float, current_price: float) -> float:
    if current_price <= 0:
        return 0.0
    
    raw_qty = usdt_amount / current_price
    precision = QUANTITY_PRECISION.get(symbol, 2)
    quantity = round(raw_qty, precision)
    
    min_qty = MIN_QUANTITY.get(symbol, 0.01)
    if quantity < min_qty:
        print(f"⚠️ Количество {quantity} меньше минимума {min_qty} для {symbol}")
        return 0.0
    
    return quantity


def get_current_price(symbol: str) -> float | None:
    endpoint = "/openApi/swap/v2/quote/price"
    params = {"symbol": symbol}
    result = bingx_request("GET", endpoint, params)

    try:
        if result.get("code") == 0:
            return float(result["data"]["price"])
    except Exception as e:
        print(f"price parse error: {e}")

    return None


def place_order(symbol: str, side: str, quantity: float, price: float | None = None):
    endpoint = "/openApi/swap/v2/trade/order"

    params = {
        "symbol": symbol,
        "side": side,
        "positionSide": "LONG" if side == "BUY" else "SHORT",
        "type": "MARKET" if USE_MARKET_ORDER else "LIMIT",
        "quantity": str(quantity),
    }

    if not USE_MARKET_ORDER and price is not None:
        params["price"] = str(price)

    return bingx_request("POST", endpoint, params)


def set_stop_loss_take_profit(symbol: str, side: str, stop_loss: float, take_profit: float):
    endpoint = "/openApi/swap/v2/trade/order"

    sl_params = {
        "symbol": symbol,
        "side": "SELL" if side == "BUY" else "BUY",
        "positionSide": "LONG" if side == "BUY" else "SHORT",
        "type": "STOP_MARKET",
        "stopPrice": str(stop_loss),
        "closePosition": "true",
    }

    tp_params = {
        "symbol": symbol,
        "side": "SELL" if side == "BUY" else "BUY",
        "positionSide": "LONG" if side == "BUY" else "SHORT",
        "type": "TAKE_PROFIT_MARKET",
        "stopPrice": str(take_profit),
        "closePosition": "true",
    }

    sl_result = bingx_request("POST", endpoint, sl_params)
    tp_result = bingx_request("POST", endpoint, tp_params)
    return sl_result, tp_result


# ==========================
#  TELEGRAM
# ==========================
def send_to_telegram(text: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    try:
        r = requests.post(url, json=payload, timeout=5)
        print(f"Telegram response: {r.status_code}")
    except Exception as e:
        print(f"Telegram error: {e}")


# ==========================
#  ROUTES
# ==========================
@app.route("/")
def home():
    return "Bot is running!", 200


@app.route("/test", methods=["GET"])
def test():
    balance = get_account_balance()
    positions = get_open_positions()
    
    return {
        "status": "OK",
        "balance": balance,
        "positions": positions,
        "settings": {
            "trading_enabled": ENABLE_TRADING,
            "position_size": POSITION_SIZE_USDT,
            "leverage": LEVERAGE,
            "api_configured": BINGX_API_KEY != "YOUR_BINGX_API_KEY",
            "supported_symbols": len(SYMBOL_MAP) // 2  # делим на 2 т.к. есть дубли с .P
        },
    }


@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        if not request.is_json:
            return "Invalid data", 400

        data = request.get_json()

        signal = data.get("signal", "N/A")
        direction = data.get("direction", "N/A")
        symbol_tv = data.get("symbol", "N/A")
        tf = data.get("tf", "N/A")

        try:
            price = float(data.get("price", 0) or 0)
        except (ValueError, TypeError):
            price = 0.0

        tp1 = data.get("tp1", "na")
        tp2 = data.get("tp2", "na")
        sl = data.get("sl", "na")

        symbol_bingx = SYMBOL_MAP.get(symbol_tv, symbol_tv)

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open("signals.log", "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {signal} {symbol_tv} → {symbol_bingx} @ {price} | {direction}\n")

        print(f"📊 Signal received: {signal} {symbol_bingx} {direction}")

        if ENABLE_TRADING and BINGX_API_KEY != "YOUR_BINGX_API_KEY":
            print(f"🤖 Auto-trading: {signal} {symbol_bingx}")

            side = "BUY" if direction == "LONG" else "SELL"

            if has_open_position(symbol_bingx, side):
                message = f"""⚠️ <b>ДУБЛЬ ПОЗИЦИИ</b>

📊 <b>Сигнал:</b> {signal}
💱 <b>Символ:</b> {symbol_bingx}
📈 <b>Направление:</b> {direction}

❌ Позиция уже открыта, сигнал пропущен

⏰ {timestamp}"""
                
                send_to_telegram(message)
                return "Position already exists", 200

            lev_result = set_leverage(symbol_bingx, LEVERAGE)
            print(f"Leverage set: {lev_result}")

            current_price = get_current_price(symbol_bingx)
            if not current_price or current_price <= 0:
                current_price = price
            
            print(f"Current price: {current_price}")

            quantity = calculate_quantity(symbol_bingx, POSITION_SIZE_USDT, current_price)
            print(f"Quantity: {quantity}")

            if quantity <= 0:
                min_qty = MIN_QUANTITY.get(symbol_bingx, 0.01)
                
                message = f"""❌ <b>ОШИБКА РАЗМЕРА</b>

📊 <b>Сигнал:</b> {signal}
💱 <b>Символ:</b> {symbol_bingx}
📈 <b>Направление:</b> {direction}
💰 <b>Цена:</b> {current_price}

⚠️ Размер позиции {POSITION_SIZE_USDT} USDT слишком мал
📏 Минимум: {min_qty}
🔢 Рассчитано: {quantity}

💡 Увеличь POSITION_SIZE_USDT до 10-15 USDT

⏰ {timestamp}"""
                
                send_to_telegram(message)
                return "Quantity too small", 400
            else:
                order_result = place_order(symbol_bingx, side, quantity)
                print(f"Order result: {order_result}")

                if sl != "na" and tp1 != "na":
                    try:
                        sl_price = float(sl)
                        tp_price = float(tp1)
                        sl_res, tp_res = set_stop_loss_take_profit(symbol_bingx, side, sl_price, tp_price)
                        print(f"SL/TP set: SL={sl_res}, TP={tp_res}")
                    except (ValueError, TypeError) as e:
                        print(f"SL/TP error: {e}")

                if order_result.get("code") == 0:
                    status = "✅ ОРДЕР ОТКРЫТ"
                    order_data = order_result.get("data", {})
                    if isinstance(order_data, dict):
                        order_id = order_data.get("order", {}).get("orderId", "N/A")
                    else:
                        order_id = str(order_data)
                else:
                    status = f"❌ ОШИБКА: {order_result.get('msg', 'Unknown')}"
                    order_id = "N/A"

            message = f"""🤖 <b>AUTO TRADE</b>
{status}

📊 <b>Сигнал:</b> {signal}
💱 <b>Символ:</b> {symbol_bingx}
📈 <b>Направление:</b> {direction}
💰 <b>Цена входа:</b> {current_price}
📦 <b>Размер:</b> {POSITION_SIZE_USDT} USDT (x{LEVERAGE})
🔢 <b>Количество:</b> {quantity}

🎯 <b>Take Profit:</b>
  TP1: {tp1}
  TP2: {tp2}

🛑 <b>Stop Loss:</b> {sl}

🆔 <b>Order ID:</b> {order_id}
⏱️ <b>Таймфрейм:</b> {tf}m
⏰ {timestamp}"""
        else:
            reason = "DISABLED" if not ENABLE_TRADING else "API NOT CONFIGURED"
            message = f"""📊 <b>{signal}</b>

💱 <b>Символ:</b> {symbol_tv}
📈 <b>Направление:</b> {direction}
💰 <b>Цена входа:</b> {price}
⏱️ <b>Таймфрейм:</b> {tf}m

🎯 <b>Take Profit:</b>
  TP1: {tp1}
  TP2: {tp2}

🛑 <b>Stop Loss:</b> {sl}

⏰ {timestamp}
⚠️ Auto-trading: <b>{reason}</b>"""

        send_to_telegram(message)
        return "OK", 200

    except Exception as e:
        error_msg = f"❌ Ошибка: {str(e)}"
        print(error_msg)
        send_to_telegram(error_msg)
        return "Error", 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
