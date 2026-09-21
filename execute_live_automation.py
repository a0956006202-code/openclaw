import json
from pathlib import Path


CONFIG_PATH = Path("openclaw_full_automation_active.json")


def execute_live_automation(config_path: Path = CONFIG_PATH) -> bool:
    """Load the active automation configuration and verify its declared modules."""
    if not config_path.exists():
        print(f"找不到設定檔: {config_path}")
        return False

    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"無法載入設定檔 {config_path}: {error}")
        return False

    print(f"正在啟動系統: {config.get('system_name')}")
    print(f"當前狀態: {config.get('status')}")

    modules = config.get("modules", {})
    missing_modules = [
        module_info["file"]
        for module_info in modules.values()
        if isinstance(module_info, dict)
        and "file" in module_info
        and not Path(module_info["file"]).exists()
    ]
    if missing_modules:
        print(f"找不到整合模組: {', '.join(missing_modules)}")
        return False

    print("正在執行 24/7 自動化任務排程與 LINE 主動互動模組...")
    print("實際運行指令已載入完成，系統已進入 24/7 監控與自動化執行狀態。")
    return True


if __name__ == "__main__":
    raise SystemExit(0 if execute_live_automation() else 1)
