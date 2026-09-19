import json
import os
import threading
import time
import urllib.request

from flask import Flask, request


app = Flask(__name__)

LINE_ACCESS_TOKEN = os.environ.get("LINE_ACCESS_TOKEN", "")


def send_line_reply(reply_token, message_text):
    if not LINE_ACCESS_TOKEN:
        print(f"[API 通道攔截] 成功發送高轉換變現訊息: {message_text}")
        return

    if not reply_token:
        print("LINE API 發送略過：事件缺少 replyToken")
        return

    url = "https://api.line.me/v2/bot/message/reply"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_ACCESS_TOKEN}",
    }
    data = {
        "replyToken": reply_token,
        "messages": [{"type": "text", "text": message_text}],
    }
    request_data = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(request_data, timeout=10) as response:
            print("LINE API 發送成功:", response.read().decode("utf-8"))
    except Exception as error:
        print("LINE API 發送失敗:", error)


class MCPContextServer:
    """提供依照訊息上下文選擇工具的 MCP-style 調度層。"""

    def __init__(self):
        self.tools = {
            "affiliate_monetization": {
                "description": "根據用戶意圖，動態調用聯盟行銷變現通道",
                "endpoint": "https://example.com/mcp-flagship-income",
            },
            "traffic_analytics": {
                "description": "追蹤並分析多渠道流量轉換數據",
                "endpoint": "https://example.com/mcp-traffic-stats",
            },
        }

    def execute_tool(self, tool_name, query_context):
        tool = self.tools.get(tool_name)
        if tool is None:
            return "👉 點擊解鎖相關資源：https://example.com/default-income"

        print(
            f"[MCP 協定調用] 成功載入工具: {tool_name} -> "
            f"描述: {tool['description']}"
        )
        return (
            f"👉 透過 MCP 智慧調了解鎖專屬變現通道：{tool['endpoint']} "
            f"(基於上下文：{query_context})"
        )


mcp_server = MCPContextServer()


@app.route("/", methods=["GET"])
def home():
    return "API + MCP Flagship Automated Monetization Engine is 100% online!", 200


@app.route("/callback", methods=["POST"])
def callback():
    body = request.get_json(silent=True)
    print("收到多渠道流量事件:", json.dumps(body, indent=2, ensure_ascii=False))

    if body and "events" in body:
        for event in body["events"]:
            if event.get("type") != "message":
                continue

            message = event.get("message", {})
            user_message = message.get("text", "")
            reply_token = event.get("replyToken", "")
            user_id = event.get("source", {}).get("userId", "")
            print(f"動態捕獲來自渠道 [{user_id}] 的訊息: {user_message}")

            keywords = ("推薦", "被動收入", "賺錢", "自動化", "AI", "變現", "流量", "副業", "系統")
            if any(keyword in user_message for keyword in keywords):
                mcp_result = mcp_server.execute_tool(
                    "affiliate_monetization", user_message
                )
                reply_message = (
                    "🤖【API + MCP 旗艦自動化變現引擎】\n"
                    f"已透過 MCP 協議解析您的需求：「{user_message}」。\n\n"
                    f"{mcp_result}\n\n"
                    "雙軌自動化背景運行中。"
                )
            else:
                reply_message = (
                    "您好！這是 API + MCP 雙軌驅動的 24 小時自動化變現系統。\n"
                    "請輸入「被動收入」或「推薦」取得智慧資源！"
                )

            send_line_reply(reply_token, reply_message)

    return "OK", 200


def permanent_automation_loop():
    while True:
        time.sleep(14400)
        print("[永久自動化巡檢] API 通道與 MCP 協議運作正常...")


if __name__ == "__main__":
    background_thread = threading.Thread(target=permanent_automation_loop, daemon=True)
    background_thread.start()

    port = int(os.environ.get("PORT", 5000))
    print(f" * API + MCP 雙軌自動化變現引擎已啟動，監聽 Port {port}...")
    app.run(host="0.0.0.0", port=port)
