# OpenClaw 全球災難復原 Runbook

## 每日備份

在已安裝 `age`、`rclone` 的主機上設定：

- `BACKUP_AGE_RECIPIENT`：只放公開 age recipient。
- `BACKUP_RCLONE_DESTINATIONS`：逗號分隔的獨立 rclone remote，例如 S3 與 Cloudflare R2。
- `BACKUP_NAS_PATH`：已掛載 NAS 的本機路徑。
- `BACKUP_IPFS_ENABLED=true`：僅在主機已設定 IPFS node/遠端 pin 服務時啟用。

執行：

```sh
python data_sovereignty_backup.py backup
```

備份會產生 `.tar.gz.age` 與同名 `.manifest.json`。目前 `age` 備份的 manifest 會標示 `pqc_status: migration_required`，不可宣稱已完成後量子保護；待 audited liboqs/HSM provider 完成混合封裝、解封與輪換演練後，才可將資料分類提升為 PQC active。manifest 的 SHA-256、各目的地與 IPFS CID 必須保留並檢查；未設定加密 recipient 時，命令會失敗而不產生未加密備份。

## 一鍵還原

1. 在乾淨主機安裝 Python、`age` 與必要的應用程式依賴。
2. 將 `BACKUP_AGE_IDENTITY` 指向離線保管的私密身份檔，並取得 `.age` 備份。
3. 先核對 manifest 的 SHA-256，再執行：

```sh
python data_sovereignty_backup.py restore vault/disaster-recovery/openclaw-<timestamp>.tar.gz.age --destination /srv/openclaw-recovered
python -m compileall -q /srv/openclaw-recovered
```

4. 在備用平台重新設定支付、郵件、DNS 與 webhook secrets，執行應用程式 smoke tests，經人工確認後切換流量。

## 演練與邊界

每季在隔離目錄做一次還原演練，記錄 RPO/RTO、manifest 核對結果與缺少的供應商設定。IPFS 是內容定址封存，不等同於保密或永久可用；需另外維持 pin/節點與加密身份的離線備份。個人資料刪除請求仍須依隱私政策與法定保存義務處理，不得用備份繞過刪除流程。
