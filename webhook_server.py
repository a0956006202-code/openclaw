import os
import requests
from flask import Flask, request
from dotenv import load_dotenv
from google import genai

load_dotenv()

app = Flask(__name__)

def is_placeholder(value: str) -> bool:
    value = (value or "").strip()
    return not value or "你的" in value or "AIzaSy..." in value

gemini_key = os.getenv("GEMINI_API_KEY", "").strip().strip('"').strip("'")
line_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "").strip().strip('"').strip("'")
model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip().strip('"').strip("'")
client = genai.Client(api_key=gemini_key) if not is_placeholder(gemini_key) else None


@app.route("/", methods=['GET'])
def health_check():
    return "OpenClaw callback service is running.", 200


@app.route("/callback", methods=['GET', 'POST'])
def callback():
    if request.method == 'GET':
        return "OpenClaw callback endpoint ready.", 200

    body = request.get_json(silent=True)
    if not body:
        return "Bad Request: expected JSON body.", 400

    events = body.get('events', [])
    for event in events:
        if event.get('type') == 'message' and isinstance(event.get('message'), dict) and event['message'].get('type') == 'text':
            user_message = event['message'].get('text', '')
            reply_token = event.get('replyToken')

            print(f"收到 LINE 訊息: {user_message}")

            if client is not None:
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=f"你是 OpenClaw 智慧助理，請簡短親切地回覆使用者這則訊息：{user_message}"
                    )
                    ai_reply = response.text
                except Exception as e:
                    ai_reply = f"系統呼叫 Gemini 發生錯誤: {e}"
            else:
                ai_reply = "OpenClaw 已啟動，但尚未設定有效的 GEMINI_API_KEY，請先補齊環境變數。"

            if line_token and reply_token:
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {line_token}"
                }
                payload = {
                    "replyToken": reply_token,
                    "messages": [{"type": "text", "text": ai_reply}]
                }
                try:
                    res = requests.post(
                        "https://api.line.me/v2/bot/message/reply",
                        headers=headers,
                        json=payload,
                        timeout=10,
                    )
                    print(f"LINE 回覆狀態: {res.status_code}, 回應: {res.text}")
                except Exception as exc:
                    print(f"LINE 回覆失敗: {exc}")

            return 'OK', 200

    return 'OK', 200


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
