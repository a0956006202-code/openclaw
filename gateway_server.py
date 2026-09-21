import argparse
import json
import re
import shlex
import subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class OpenClawBridge:
    def __init__(self, openclaw_cmd, openclaw_timeout, session_id, token):
        self.openclaw_cmd = openclaw_cmd
        self.openclaw_timeout = openclaw_timeout
        self.session_id = session_id
        self.token = token

    def parse_text_to_plan(self, text: str, device_snapshot: list) -> dict:
        prompt = (
            f"設備狀態: {json.dumps(device_snapshot, ensure_ascii=False)}\n"
            f"用戶輸入文本: {text}\n"
            "你必須只輸出 JSON 對象，不要輸出其他文字。\n"
            "你輸出的 json 有兩種格式：\n"
            "1) 順序執行: {'commands':['CMD1','CMD2'], 'reason':'...'}\n"
            "2) 平行執行: {'parallel':[{'device':'servo','command':'...'}, ...], 'reason':'...'}\n"
            "commands 中的每一項必須是命令，允許的命令格式：\n"
            "* STATUS, HELP, PING, LED ON, LED OFF, LED BLINK <50-5000>,\n"
            "* BEEP ON, BEEP OFF, BEEP TOGGLE, BEEP <10-1000>,\n"
            "* SERVO <0-180>, WAIT <50-2000>,\n"
            "* SERVO SWEEP START <0-180> <0-180> <50-2000>, SERVO SWEEP STOP,\n"
            "SERVO SWEEP STATUS。\n"
            "結果數值要自動裁剪到合法範圍。"
        )
        command = shlex.split(self.openclaw_cmd) + [
            "agent",
            "local",
            "--session-id",
            self.session_id,
            "--message",
            prompt,
            "--json",
        ]
        process = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=self.openclaw_timeout,
            check=False,
        )
        if process.returncode != 0:
            raise RuntimeError(f"OpenClaw 錯誤: {process.stderr.strip()}")
        return json.loads(process.stdout.strip())


class GatewayHandler(BaseHTTPRequestHandler):
    bridge: OpenClawBridge = None

    def _send_json(self, code: int, payload: dict):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.end_headers()

    def normalize_commands(self, raw_commands: list) -> list:
        allowed = []
        for raw_command in raw_commands:
            command = str(raw_command).strip().upper()
            if (
                command in ("STATUS", "HELP", "PING", "SERVO SWEEP STOP", "SERVO SWEEP STATUS")
                or re.fullmatch(r"LED (ON|OFF|BLINK \d+)", command)
                or re.fullmatch(r"BEEP (ON|OFF|TOGGLE|\d+)", command)
                or re.fullmatch(r"SERVO \d+", command)
                or re.fullmatch(r"WAIT \d+", command)
                or re.fullmatch(r"SERVO SWEEP START \d+ \d+ \d+", command)
            ):
                allowed.append(command)
        return allowed[:8]

    def _authorized(self) -> bool:
        if not self.bridge.token:
            return True
        return self.headers.get("Authorization", "") == f"Bearer {self.bridge.token}"

    def do_POST(self):
        if self.path != "/api/brain":
            self._send_json(404, {"code": 404, "msg": "not found", "data": None})
            return
        if not self._authorized():
            self._send_json(401, {"code": 401, "msg": "unauthorized", "data": None})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            data = json.loads(self.rfile.read(length).decode("utf-8"))
            text = data.get("text", "").strip()
            if not text:
                self._send_json(400, {"code": 400, "msg": "缺少 text 字段", "data": None})
                return
            plan = self.bridge.parse_text_to_plan(text, data.get("device_snapshot", []))
            safe_commands = self.normalize_commands(plan.get("commands", []))
            self._send_json(
                200,
                {
                    "code": 200,
                    "msg": "ok",
                    "data": {"plan": plan, "executed_commands": safe_commands},
                },
            )
        except Exception as error:
            self._send_json(500, {"code": 500, "msg": str(error), "data": None})


def main():
    parser = argparse.ArgumentParser(description="LARK gateway for CONSK servo control")
    parser.add_argument("--host", default="0.0.0.0", help="監聽地址")
    parser.add_argument("--port", type=int, default=18789, help="監聽端口")
    parser.add_argument("--token", default="", help="Bearer 鑑權密鑰")
    parser.add_argument("--openclaw-cmd", default="openclaw", help="OpenClaw 可執行命令")
    parser.add_argument("--openclaw-timeout", type=float, default=45.0, help="OpenClaw 單輪超時")
    parser.add_argument("--openclaw-session-id", default="stm32-mobile-brain", help="OpenClaw 會話 ID")
    args = parser.parse_args()

    GatewayHandler.bridge = OpenClawBridge(
        args.openclaw_cmd, args.openclaw_timeout, args.openclaw_session_id, args.token
    )
    server = ThreadingHTTPServer((args.host, args.port), GatewayHandler)
    print(f"Gateway server running on {args.host}:{args.port}...")
    server.serve_forever()


if __name__ == "__main__":
    main()
