import logging


logger = logging.getLogger("MindShield")


class WatchdogMindShield:
    def filter_notifications(self, logs: list) -> list:
        critical_alerts = [
            log for log in logs if log.get("severity") == "CRITICAL"
        ]
        logger.info(
            f"Filtered {len(logs)} background logs. Suppressing noise, "
            f"forwarding {len(critical_alerts)} critical decisions."
        )
        return critical_alerts
