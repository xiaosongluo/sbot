import hmac
import hashlib
import base64
import time
import urllib.parse
from datetime import datetime, timezone, timedelta

import requests


def sign_dingtalk_secret(secret):
    timestamp = str(round(time.time() * 1000))
    string_to_sign = f"{timestamp}\n{secret}"
    hmac_code = hmac.new(
        secret.encode("utf-8"), string_to_sign.encode("utf-8"), hashlib.sha256
    ).digest()
    return timestamp, urllib.parse.quote_plus(base64.b64encode(hmac_code))


def beijing_time():
    utc_now = datetime.utcnow().replace(tzinfo=timezone.utc)
    return utc_now.astimezone(timezone(timedelta(hours=8))).strftime("%d/%m %H:%M:%S")


def send_dingtalk_notification(message, secret, token):
    ts, sign = sign_dingtalk_secret(secret)
    url = f"https://oapi.dingtalk.com/robot/send?access_token={token}&sign={sign}&timestamp={ts}"

    headers = {"Content-Type": "application/json"}
    payload = {
        "msgtype": "markdown",
        "markdown": {"title": "📢 Telegram同步通知", "text": message},
    }

    response = requests.post(url, json=payload, headers=headers, timeout=5)
    return response.json()