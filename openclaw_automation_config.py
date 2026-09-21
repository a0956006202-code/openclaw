import json
from pathlib import Path


AUTOMATION_CONFIG = {
    "target_goal": "實現 24 小時全自動化日常任務、訊息處理與資料管理",
    "automation_modes": [
        {
            "mode": "AI 代理與聊天機器人整合 (例如 Manus 結合 LINE)",
            "features": [
                "直接在通訊軟體中執行多步驟任務、處理檔案與資料",
                "透過綁定帳號，讓 AI 自動處理日常交辦事項",
            ],
        },
        {
            "mode": "自動化工作流程平台 (例如 Make、Zapier、n8n)",
            "features": [
                "串接常用服務 (如 Gmail、Google 雲端硬碟、LINE、Notion)",
                "設定觸發條件與動作，實現郵件自動備份與跨應用通知",
            ],
        },
        {
            "mode": "內建指令與腳本 (如 Google Apps Script、Python API)",
            "features": [
                "處理自訂邏輯、郵件自動分類、試算表資料更新",
                "透過排程定時執行特定任務",
            ],
        },
    ],
}


def write_automation_config(output_path: str = "openclaw_automation_config.json") -> Path:
    path = Path(output_path)
    path.write_text(
        json.dumps(AUTOMATION_CONFIG, indent=4, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"已成功將全自動化選項與設定寫入指令檔：{path}")
    return path


if __name__ == "__main__":
    write_automation_config()
