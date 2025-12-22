from flask import Flask, request
import requests
import hmac
import hashlib
import time
from datetime import datetime

app = Flask(__name__)

# ==========================
#  TELEGRAM
# ==========================
BOT_TOKEN = "8337671886:AAFQk7A6ZYhgu63l9C2cmAj3meTJa7RD3b4"
CHAT_ID = "5411759224"

# ==========================
#  BINGX API
# ==========================
BINGX_API_KEY = "0Vlr5cQ6Sut9R8yj4a739rbpS5DUDpzloLIPgbV8SX0XvChY6HkRFlD6YXu4y3cl3BJOCoLL8RLgeIEBeA"
BINGX_SECRET_KEY = "N5jgsWdsH4BEAvfzz3ehudturqXSEWjYNCpGo6N8brdXRl11YgkCSwpPbHy48DtBGHMjg7ywkcJY7eOdy43nQ"

BINGX_BASE_URL = "https://open-api.bingx.com"

# ==========================
#  НАСТРОЙКИ ТОРГОВЛИ
# ==========================
ENABLE_TRADING = True        # <<< ВКЛЮЧИТЬ ТОРГОВЛЮ
POSITION_SIZE_USDT = 5       # размер позиции 5 USDT
LEVERAGE = 10                  # плечо 10
USE_MARKET_ORDER = True       # True = маркет, False = лимит

# ==========================
#  СООТВЕТСТВИЕ СИМВОЛОВ
# ==========================
SYMBOL_MAP = {
    # Стандартные символы
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
}

# Precision для разных символов (количество знаков после запятой)
QUANTITY_PRECISION = {
    "BTC-USDT": 3,   # 0.001
    "ETH-USDT": 2,   # 0.01
    "BNB-USDT": 2,
    "SOL-USDT": 1,
    "XRP-USDT": 0,   # целое число
    "ADA-USDT": 0,
    "DOGE-USDT": 0,
    "AVAX-USDT": 1,
    "MATIC-USDT": 0,
    "DOT-USDT": 1,
    "TRX-USDT": 0,
    "LINK-USDT": 1,
}

# ==========================
#  ФУНКЦИИ BINGX
# ==========================
def create_signature(params: dict, secret_key: str) -> str:
    """Создание подписи для BingX"""
    query_string = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
    return hmac.new(
        secret_key.encode("utf-8"),
        query_string.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def bingx_request(method: str, endpoint: str, params: dict | None = None) -> dict:
    """Универсальный запрос к BingX"""
    if params is None:
        params = {}

    # timestamp обязателен
    params["timestamp"] = int(time.time() * 1000)

    # подпись
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
            # BingX требует params в query string для POST тоже
            r = requests.post(url, params=params, headers=headers, timeout=10)
        else:
            r = requests.request(method, url, params=params, headers=headers, timeout=10)

        response = r.json()
        print(f"BingX response: {response}")  # для отладки
        return response
    except Exception as e:
        print(f"BingX error: {e}")
        return {"code": -1, "msg": str(e)}


def get_account_balance():
    endpoint = "/openApi/swap/v2/user/balance"
    return bingx_request("GET", endpoint)


def set_leverage(symbol: str, leverage: int):
    endpoint = "/openApi/swap/v2/trade/leverage"
    params = {
        "symbol": symbol,
        "side": "BOTH",
        "leverage": leverage,
    }
    return bingx_request("POST", endpoint, params)


def calculate_quantity(symbol: str, usdt_amount: float, current_price: float) -> float:
    """Рассчитать количество с правильной точностью"""
    if current_price <= 0:
        return 0.0
    
    raw_qty = usdt_amount / current_price
    precision = QUANTITY_PRECISION.get(symbol, 2)  # по умолчанию 2 знака
    
    return round(raw_qty, precision)


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
        "side": side,  # BUY / SELL
        "positionSide": "LONG" if side == "BUY" else "SHORT",
        "type": "MARKET" if USE_MARKET_ORDER else "LIMIT",
        "quantity": str(quantity),  # BingX требует строку
    }

    if not USE_MARKET_ORDER and price is not None:
        params["price"] = str(price)

    return bingx_request("POST", endpoint, params)


def set_stop_loss_take_profit(symbol: str, side: str, stop_loss: float, take_profit: float):
    """Установка SL и TP"""
    endpoint = "/openApi/swap/v2/trade/order"

    # Stop Loss
    sl_params = {
        "symbol": symbol,
        "side": "SELL" if side == "BUY" else "BUY",
        "positionSide": "LONG" if side == "BUY" else "SHORT",
        "type": "STOP_MARKET",
        "stopPrice": str(stop_loss),
        "closePosition": "true",
    }

    # Take Profit
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
    """Тестовый endpoint"""
    balance = get_account_balance()
    return {
        "status": "OK",
        "balance": balance,
        "settings": {
            "trading_enabled": ENABLE_TRADING,
            "position_size": POSITION_SIZE_USDT,
            "leverage": LEVERAGE,
            "api_configured": BINGX_API_KEY != "YOUR_BINGX_API_KEY"
        },
    }


@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        if not request.is_json:
            return "Invalid data", 400

        data = request.get_json()

        # Парсим данные
        signal = data.get("signal", "N/A")
        direction = data.get("direction", "N/A")
        symbol_tv = data.get("symbol", "N/A")
        tf = data.get("tf", "N/A")

        # Безопасный парсинг цены
        try:
            price = float(data.get("price", 0) or 0)
        except (ValueError, TypeError):
            price = 0.0

        tp1 = data.get("tp1", "na")
        tp2 = data.get("tp2", "na")
        sl = data.get("sl", "na")

        # Конвертация символа
        symbol_bingx = SYMBOL_MAP.get(symbol_tv)
        if not symbol_bingx:
            print(f"Unknown symbol: {symbol_tv}")
            symbol_bingx = symbol_tv  # используем как есть

        # Логирование
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open("signals.log", "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {signal} {symbol_tv} → {symbol_bingx} @ {price} | {direction}\n")

        print(f"📊 Signal received: {signal} {symbol_bingx} {direction}")

        # ==========================
        #  ТОРГОВЛЯ
        # ==========================
        if ENABLE_TRADING and BINGX_API_KEY != "YOUR_BINGX_API_KEY":
            print(f"🤖 Auto-trading: {signal} {symbol_bingx}")

            # 1. Установить плечо
            lev_result = set_leverage(symbol_bingx, LEVERAGE)
            print(f"Leverage set: {lev_result}")

            # 2. Получить цену
            current_price = get_current_price(symbol_bingx)
            if not current_price or current_price <= 0:
                current_price = price
            
            print(f"Current price: {current_price}")

            # 3. Рассчитать количество
            quantity = calculate_quantity(symbol_bingx, POSITION_SIZE_USDT, current_price)
            print(f"Quantity: {quantity}")

            if quantity <= 0:
                status = "❌ ОШИБКА: Неверное количество"
                order_id = "N/A"
            else:
                # 4. Разместить ордер
                side = "BUY" if direction == "LONG" else "SELL"
                order_result = place_order(symbol_bingx, side, quantity)
                print(f"Order result: {order_result}")

                # 5. Установить SL/TP
                if sl != "na" and tp1 != "na":
                    try:
                        sl_price = float(sl)
                        tp_price = float(tp1)
                        sl_res, tp_res = set_stop_loss_take_profit(symbol_bingx, side, sl_price, tp_price)
                        print(f"SL/TP set: SL={sl_res}, TP={tp_res}")
                    except (ValueError, TypeError) as e:
                        print(f"SL/TP error: {e}")

                # Проверка результата
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
⏱ <b>Таймфрейм:</b> {tf}m
⏰ {timestamp}"""
        else:
            # Только уведомление
            reason = "DISABLED" if not ENABLE_TRADING else "API NOT CONFIGURED"
            message = f"""📊 <b>{signal}</b>

💱 <b>Символ:</b> {symbol_tv}
📈 <b>Направление:</b> {direction}
💰 <b>Цена входа:</b> {price}
⏱ <b>Таймфрейм:</b> {tf}m

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





