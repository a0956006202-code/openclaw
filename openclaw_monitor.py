import logging
import time
import traceback
from functools import wraps


logging.basicConfig(
    filename="openclaw_run.log",
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    encoding="utf-8",
)


def safe_run(max_retries=3, delay=5):
    """為 OpenClaw 自動化任務提供重試與日誌記錄。"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            while attempts < max_retries:
                try:
                    logging.info(
                        "開始執行任務: %s (第 %s 次嘗試)",
                        func.__name__,
                        attempts + 1,
                    )
                    result = func(*args, **kwargs)
                    logging.info("任務成功完成: %s", func.__name__)
                    return result
                except Exception as error:
                    attempts += 1
                    error_msg = traceback.format_exc()
                    logging.error(
                        "任務 %s 發生錯誤 (嘗試 %s/%s): %s\n%s",
                        func.__name__,
                        attempts,
                        max_retries,
                        error,
                        error_msg,
                    )
                    if attempts < max_retries:
                        time.sleep(delay)
                    else:
                        logging.critical(
                            "任務 %s 已達最大重試次數，強制終止。",
                            func.__name__,
                        )
                        raise

        return wrapper

    return decorator


@safe_run(max_retries=3, delay=2)
def sample_openclaw_task():
    """範例 OpenClaw 自動化任務。"""
    print("正在執行 OpenClaw 自動化任務...")
    return "執行成功"


if __name__ == "__main__":
    print("OpenClaw 監控與日誌模組已啟動！")
    sample_openclaw_task()