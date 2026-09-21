import os
import requests

token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
user_id = os.getenv("LINE_USER_ID")

if not token or not user_id or "真實" in token:
    print("錯誤：尚未設定真實的 LINE_CHANNEL_ACCESS_TOKEN 或 LINE_USER_ID 環境變數！")
else:
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    payload = {
        "to": user_id,
        "messages": [{"type": "text", "text": "Hello, OpenClaw is fully connected!"}],
    }
    res = requests.post(url, headers=headers, json=payload)
    print(f"Status Code: {res.status_code}")
    print(f"Response: {res.text}")
