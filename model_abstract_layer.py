import logging


logger = logging.getLogger("ModelRouter")


class ModelAgnosticLayer:
    def __init__(self, primary_model: str, backup_model: str):
        self.current_model = primary_model
        self.backup_model = backup_model

    def inference(self, prompt: str):
        try:
            raise ConnectionError("Primary API provider down.")
        except Exception:
            logger.warning(
                "Primary model failed. Hot-swapping to fallback local model: "
                f"{self.backup_model}"
            )
            return f"[Fallback Response using {self.backup_model}]"
