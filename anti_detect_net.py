import logging
import random


logger = logging.getLogger("AntiDetect")


class AntiDetectProxyPool:
    def __init__(self, proxies: list):
        self.proxies = proxies

    def get_stealth_session_config(self):
        proxy = random.choice(self.proxies)
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        }
        logger.info(
            f"Assigned stealth proxy: {proxy[:6]}... "
            "with randomized browser fingerprint."
        )
        return {"proxy": proxy, "headers": headers}
