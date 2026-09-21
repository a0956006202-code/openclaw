import argparse
import sys


def main():
    parser = argparse.ArgumentParser(
        description="LARK gateway for CONSK servo control"
    )
    parser.add_argument("--host", default="0.0.0.0", help="監聽地址")
    parser.add_argument("--port", type=int, default=18789, help="監聽端口")
    parser.add_argument(
        "--serial-port",
        default="/dev/cu.usbserial-3120",
        help="串口設備路徑",
    )
    parser.add_argument("--baud", type=int, default=115200, help="串口波特率")
    parser.add_argument(
        "--serial-timeout",
        type=float,
        default=0.5,
        help="串口讀取超時時間",
    )
    parser.add_argument("--token", default="", help="Bearer 鑑權密鑰")
    parser.add_argument(
        "--openclaw-cmd",
        default="node /Users/luojingjiedemac/gitcode_obj/biyasheji/emdash-app/openclaw/openclaw.mjs",
        help="OpenClaw 可執行命令路徑",
    )
    parser.add_argument(
        "--openclaw-timeout",
        type=float,
        default=45.0,
        help="OpenClaw 單輪超時",
    )
    parser.add_argument(
        "--openclaw-session-id",
        default="stm32-mobile-brain",
        help="OpenClaw 會話 ID",
    )

    args = parser.parse_args()
    print(
        f"Starting gateway on {args.host}:{args.port}, "
        f"serial port: {args.serial_port}"
    )


if __name__ == "__main__":
    main()
