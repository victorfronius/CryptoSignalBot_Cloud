from flask import Flask, request, jsonify
import requests
import hmac
import hashlib
import time
import os

app = Flask(__name__)

# API КЛЮЧИ
BINGX_API_KEY = "tfi2cWlGNK9eSpDJlxNks2w7DBiT6lTlUiXLjkBQhe7sIgVv7HKWiByVhDSagmrZBSgb8Hoaog1N4HzYffQ"
BINGX_SECRET_KEY = "SnNoEvoc1ZBhwHYMzi1KfAIvvgnI8eWs6b4fyjo9i7u0pcsHijJ7YIEngeHUVD19YxLeyrp2yE9UPjYAqM65w"
BINGX_BASE_URL = "https://open-api.bingx.com"

def sign(params: dict) -> str:
    """Создаёт подпись для BingX"""
    query_string = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
    signature = hmac.new(
        BINGX_SECRET_KEY.encode(),
        query_string.encode(),
        hashlib.sha256
    ).hexdigest()
    
    print(f"=== DEBUG SIGNATURE ===")
    print(f"Query String: {query_string}")
    print(f"Secret Key Length: {len(BINGX_SECRET_KEY)}")
    print(f"Signature: {signature}")
    print(f"======================")
    
    return signature

def bingx_test():
    """Тестовый запрос к BingX"""
    endpoint = "/openApi/swap/v2/user/balance"
    
    params = {
        "timestamp": int(time.time() * 1000),
        "recvWindow": 60000
    }
    
    params["signature"] = sign(params)
    
    headers = {
        "X-BX-APIKEY": BINGX_API_KEY
    }
    
    url = BINGX_BASE_URL + endpoint
    
    print(f"\n=== REQUEST ===")
    print(f"URL: {url}")
    print(f"Headers: {headers}")
    print(f"Params: {params}")
    print(f"===============\n")
    
    try:
        r = requests.get(url, params=params, headers=headers, timeout=10)
        response = r.json()
        
        print(f"\n=== RESPONSE ===")
        print(f"Status: {r.status_code}")
        print(f"Response: {response}")
        print(f"================\n")
        
        return response
    except Exception as e:
        print(f"ERROR: {e}")
        return {"code": -1, "msg": str(e)}

@app.route("/")
def home():
    return """
    <h1>BingX Debug Tool</h1>
    <p>Тестовый инструмент для отладки API</p>
    <ul>
        <li><a href="/test">/test</a> - Тест баланса</li>
        <li><a href="/check_keys">/check_keys</a> - Проверка ключей</li>
    </ul>
    """

@app.route("/test")
def test():
    result = bingx_test()
    return jsonify(result)

@app.route("/check_keys")
def check_keys():
    return jsonify({
        "api_key_length": len(BINGX_API_KEY),
        "secret_key_length": len(BINGX_SECRET_KEY),
        "api_key_first_10": BINGX_API_KEY[:10],
        "api_key_last_10": BINGX_API_KEY[-10:],
        "secret_key_first_10": BINGX_SECRET_KEY[:10],
        "secret_key_last_10": BINGX_SECRET_KEY[-10:],
        "has_spaces_api": " " in BINGX_API_KEY,
        "has_spaces_secret": " " in BINGX_SECRET_KEY
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
