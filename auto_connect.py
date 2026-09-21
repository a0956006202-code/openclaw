import os
import requests

print("--- OpenClaw 智慧連線診斷與打通程式 ---")

# 嘗試自動讀取 .env 或系統環境變數
token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "").strip()
user_id = os.getenv("LINE_USER_ID", "").strip()

if os.path.exists(".env"):
    with open(".env", "r") as f:
        for line in f:
            if "=" in line and not line.startswith("#"):
                k, v = line.strip().split("=", 1)
                if k.strip() == "LINE_CHANNEL_ACCESS_TOKEN" and not token:
                    token = v.strip().strip("\"'")
                elif k.strip() == "LINE_USER_ID" and not user_id:
                    user_id = v.strip().strip("\"'")

if not token or "YOUR_" in token or "真實" in token or "Channel" in token:
    print("\n[提示] 尚未偵測到有效的真實 LINE Channel Access Token。")
    token = input("請直接貼上您的真實 Channel Access Token: ").strip()

if not user_id or "YOUR_" in user_id or "真實" in user_id or "User" in user_id:
    print("\n[提示] 尚未偵測到有效的真實 LINE User ID。")
    user_id = input("請直接貼上您的真實 LINE User ID: ").strip()

if token and user_id:
    print("\n正在向 LINE API 發送測試推播...")
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    payload = {
        "to": user_id,
        "messages": [{"type": "text", "text": "Hello, OpenClaw connection is fully successful and connected!"}]
    }

    try:
        res = requests.post(url, headers=headers, json=payload)
        print(f"Status Code: {res.status_code}")
        print(f"Response: {res.text}")
        if res.status_code == 200:
            print("\n🎉 恭喜！LINE API 已經完全打通，請檢查您的手機 LINE 是否收到訊息！")
        else:
            print("\n⚠️ 發送失敗，請確認您的 Token 與 User ID 是否正確。")
    except Exception as e:
        print(f"發送過程發生錯誤: {e}")
else:
    print("❌ 憑證不完整，無法發送測試。")
