import json
import os


paths = [
    os.path.expanduser("~/.vscode-remote/data/Machine/settings.json"),
    os.path.expanduser("~/.vscode/settings.json"),
    ".vscode/settings.json",
]

for path in paths:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    try:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file) if os.path.exists(path) else {}
    except (OSError, json.JSONDecodeError):
        data = {}

    data["github.copilot.advanced"] = {"chatModel": "gpt-4o"}
    data["chat.model.default"] = "gpt-4o"
    data["github.copilot.enable"] = {"*": False}

    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

print("環境已自動補強並鎖定安全模型！")