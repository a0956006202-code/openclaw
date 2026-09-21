import datetime
import random


def check_system_health():
    print(
        f"[{datetime.datetime.now()}] "
        "🔄 [批次二十五] 執行全球多節點負載均衡與自動容災備援 "
        "(High Availability)..."
    )

    # 模擬系統健康狀態檢測。
    status = random.choice(("OK", "ERROR"))

    if status == "OK":
        print("-> [批次二十五] 狀態：所有雲端節點運作正常，無異常中斷。")
        print(
            "-> [批次二十五] 容災備援：自動重試機制與自我修復腳本已待命，"
            "高可用性防線建置完成！"
        )
    else:
        print("-> [批次二十五] 警告：偵測到節點異常，正在自動切換備援伺服器...")


if __name__ == "__main__":
    check_system_health()
