import json
import os
import urllib.error
import urllib.request


LINE_PUSH_URL = "https://api.line.me/v2/bot/message/push"


def send_line_message(user_id: str, token: str, message: str) -> None:
    """Send one text message through the LINE Messaging API."""
    payload = {
        "to": user_id,
        "messages": [{"type": "text", "text": message}],
    }
    request = urllib.request.Request(
        LINE_PUSH_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request) as response:
            if response.status == 200:
                print("LINE 主動推播訊息成功！")
            else:
                print(f"發送失敗，狀態碼: {response.status}")
    except urllib.error.HTTPError as error:
        details = error.read().decode("utf-8", errors="replace")
        print(f"LINE API 發送失敗，狀態碼: {error.code}，回應: {details}")
    except urllib.error.URLError as error:
        print(f"網路連線錯誤: {error.reason}")


if __name__ == "__main__":
    channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "").strip()
    user_id = os.getenv("LINE_USER_ID", "").strip()

    if not channel_access_token or not user_id:
        raise SystemExit(
            "請先設定 LINE_CHANNEL_ACCESS_TOKEN 與 LINE_USER_ID 環境變數。"
        )

    send_line_message(
        user_id,
        channel_access_token,
        "哈囉！這是 OpenClaw 系統主動傳給你的聊天訊息。",
    )
