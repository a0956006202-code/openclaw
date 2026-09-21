import os
import requests

# 這裡可以直接把您的真實 Token 與 User ID 帶進來測試，或讀取環境變數
TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "請替換為您的真實Channel Access Token")
USER_ID = os.getenv("LINE_USER_ID", "請替換為您的真實LINE User ID")

if not TOKEN.isascii() or not USER_ID.isascii():
    raise SystemExit("請先設定 LINE_CHANNEL_ACCESS_TOKEN 與 LINE_USER_ID 環境變數")

url = "https://api.line.me/v2/bot/message/push"
headers = {
        "Content-Type": "application/json",
            "Authorization": f"Bearer {TOKEN}"
}
payload = {
        "to": USER_ID,
            "messages": [{"type": "text", "text": "Hello, OpenClaw connection is fully successful!"}]
}

response = requests.post(url, headers=headers, json=payload)
print(f"Status Code: {response.status_code}")
print(f"Response: {response.text}")
