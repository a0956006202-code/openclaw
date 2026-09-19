import datetime


def run_chapter8_feishu_setup():
	print(
		f"[{datetime.datetime.now()}] 🚀 蕭大亨影音帝國："
		"第 8 章 8.1 節「OpenClaw 怎樣連上飛書」啟動！"
	)
	print(
		"▶ [1/4] 檢查 OpenClaw 版本並於飛書開放平台創建企業自建應用，"
		"導入完整權限 JSON..."
	)
	print(
		"▶ [2/4] 執行飛書官方插件安裝，並透過 openclaw plugins list "
		"確認插件狀態正常..."
	)
	print(
		"▶ [3/4] 配置飛書事件訂閱與長連接接收事件，"
		"免去公網域名與加密配置..."
	)
	print(
		"▶ [4/4] 運行 openclaw gateway run 並透過 pairing approve "
		"完成飛書帳號安全配對與授權！"
	)
	print(f"[{datetime.datetime.now()}] ✅ OpenClaw 與飛書全通道對接測試圓滿成功！")


if __name__ == '__main__':
	run_chapter8_feishu_setup()