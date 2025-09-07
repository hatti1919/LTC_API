LTC Wallet API

Pythonで簡単にLitecoin（LTC）の残高取得・送金・履歴確認ができる自作APIです。  


---

# インストール

```bash
git clone https://github.com/［user name］/LTC_API.git
cd LTC_API

pip install pycoin
pip install requests 

```

# 使い方

```bash 

BLOCKCYPHER_TOKEN = "token"

```
ltc_wallet_apiにあるtokenをBLOCKCYPHERのトークンに置き換え
※無料版だと制限が厳しいです。残高やログが取得できない場合制限にしてません。

# 呼び出し例

## ウォレット作成

```bash 
from ltc_wallet_api import create_wallet
user_id = "example_user"
address, wif = create_wallet(user_id)
print("アドレス:", address)
```
ウォレットを作成する関数を呼び出している。

## 残高取得
```bash 
from ltc_wallet_api import get_balance
balance_ltc, balance_jpy = get_balance(user_id)
print("残高:", balance_ltc, "LTC /", balance_jpy, "JPY")
```
残高を取得する。現在の残高を正確に把握します
jpy表記もできます

## LTC送金

```bash 

from ltc_wallet_api import send_ltc

success, result = send_ltc("test_user", "送金先アドレス", 1000)  # 1000円分
print("送金成功:", success)
print("結果:", result)

```
# ライセンス

```bash
MIT License

Copyright (c) 2025 husiri

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
