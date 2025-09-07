# ltc_wallet_api.py
import json, os, secrets, requests
from datetime import datetime
from pycoin.symbols.ltc import network

DB_FILE = "wallets.json"
COINGECKO_API = "https://api.coingecko.com/api/v3/simple/price?ids=litecoin&vs_currencies=jpy"
BLOCKCYPHER_API = "https://api.blockcypher.com/v1/ltc/main"
BLOCKCYPHER_TOKEN = "token"  # ←ここにAPIトークン

# ----------------- ウォレット管理 -----------------
def load_wallets():
    if os.path.exists(DB_FILE):
        with open(DB_FILE,"r") as f:
            return json.load(f)
    return {}

def save_wallets(wallets):
    with open(DB_FILE,"w") as f:
        json.dump(wallets,f,indent=2)

def wallet_exists(user_id: str) -> bool:
    wallets = load_wallets()
    return user_id in wallets

def create_wallet(user_id: str):
    wallets = load_wallets()
    if user_id in wallets:
        return wallets[user_id]["address"], wallets[user_id]["wif"]

    secret_exponent = secrets.randbits(256)
    key = network.keys.private(secret_exponent=secret_exponent)
    addr, wif = key.address(), key.wif()
    wallets[user_id] = {
        "address": addr,
        "wif": wif,
        "balance_ltc": 0,
        "balance_jpy": 0,
        "history": []
    }
    save_wallets(wallets)
    return addr, wif

def get_address(user_id: str):
    wallets = load_wallets()
    return wallets[user_id]["address"] if user_id in wallets else None

def get_rate():
    try:
        res = requests.get(COINGECKO_API, timeout=5).json()
        return res["litecoin"]["jpy"]
    except:
        return 40000  # デフォルト値

# ----------------- ブロックチェーン同期 -----------------
def update_balance_and_history(user_id: str):
    wallets = load_wallets()
    if user_id not in wallets:
        return 0,0,[]

    addr = wallets[user_id]["address"]
    try:
        res = requests.get(f"{BLOCKCYPHER_API}/addrs/{addr}/full?token={BLOCKCYPHER_TOKEN}", timeout=10).json()
        total_received = sum([tx["outputs"][0]["value"] for tx in res.get("txs", []) if addr in tx["outputs"][0]["addresses"]])/1e8
        total_sent = sum([tx["inputs"][0]["output_value"] for tx in res.get("txs", []) if addr in tx["inputs"][0]["addresses"]])/1e8
        balance_ltc = total_received - total_sent

        rate = get_rate()
        balance_jpy = balance_ltc * rate

        # 履歴作成（最新10件）
        history = []
        for tx in res.get("txs", [])[-10:]:
            # 入金か送金か判定
            inputs_addr = [inp["addresses"][0] for inp in tx.get("inputs",[])]
            outputs_addr = [out["addresses"][0] for out in tx.get("outputs",[])]
            if addr in outputs_addr and addr not in inputs_addr:
                # 入金
                amt_ltc = sum([out["value"] for out in tx["outputs"] if addr in out["addresses"]])/1e8
                history.append({
                    "type": "receive",
                    "amount_ltc": amt_ltc,
                    "amount_jpy": amt_ltc*rate,
                    "timestamp": tx.get("confirmed", datetime.utcnow().isoformat()),
                    "txid": tx["hash"],
                    "to": "-"
                })
            elif addr in inputs_addr:
                # 出金
                amt_ltc = sum([out["value"] for out in tx["outputs"] if addr not in out["addresses"]])/1e8
                to_addr = [out["addresses"][0] for out in tx["outputs"] if addr not in out["addresses"]][0]
                history.append({
                    "type": "send",
                    "amount_ltc": amt_ltc,
                    "amount_jpy": amt_ltc*rate,
                    "timestamp": tx.get("confirmed", datetime.utcnow().isoformat()),
                    "txid": tx["hash"],
                    "to": to_addr
                })

        # JSONに保存
        wallets[user_id]["balance_ltc"] = balance_ltc
        wallets[user_id]["balance_jpy"] = balance_jpy
        wallets[user_id]["history"] = history
        save_wallets(wallets)
        return balance_ltc, balance_jpy, history
    except Exception as e:
        print("Error updating balance:", e)
        return wallets[user_id]["balance_ltc"], wallets[user_id]["balance_jpy"], wallets[user_id]["history"]

def get_balance(user_id: str):
    balance_ltc, balance_jpy, _ = update_balance_and_history(user_id)
    return balance_ltc, balance_jpy

def get_history(user_id: str):
    _, _, history = update_balance_and_history(user_id)
    return history

# ----------------- 送金 -----------------
def send_ltc(user_id: str, to_address: str, amount_jpy: float):
    wallets = load_wallets()
    if user_id not in wallets:
        return False, "ウォレットが存在しません。"

    rate = get_rate()
    amt_ltc = amount_jpy / rate
    from_address, wif = wallets[user_id]["address"], wallets[user_id]["wif"]

    # 固定手数料0.0001 LTC
    fee_ltc = 0.00003
    if amt_ltc + fee_ltc > wallets[user_id]["balance_ltc"]:
        return False, f"残高不足: 残高{wallets[user_id]['balance_ltc']:.8f} LTC"

    url = f"{BLOCKCYPHER_API}/txs/new?token={BLOCKCYPHER_TOKEN}"
    data = {
        "inputs":[{"addresses":[from_address]}],
        "outputs":[{"addresses":[to_address],"value":int(amt_ltc*1e8)}],
        "fees": int(fee_ltc*1e8)
    }

    try:
        res = requests.post(url, json=data, timeout=10).json()
        if "errors" in res:
            return False, res["errors"]

        tx, tosign = res["tx"], res["tosign"]
        key = network.parse.wif(wif)
        signatures = [key.sign(bytes.fromhex(s)).hex() for s in tosign]
        pubkeys = [key.sec().hex() for _ in tosign]
        send_data = {"tx":tx,"tosign":tosign,"signatures":signatures,"pubkeys":pubkeys}
        final = requests.post(f"{BLOCKCYPHER_API}/txs/send?token={BLOCKCYPHER_TOKEN}", json=send_data, timeout=10).json()
        txid = final.get("tx",{}).get("hash","unknown_txid")

        # 残高更新
        update_balance_and_history(user_id)
        return True, txid
    except Exception as e:
        return False, str(e)
