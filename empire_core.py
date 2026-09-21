import asyncio
import logging
import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [DigitalEmpire] %(message)s",
)
logger = logging.getLogger("EmpireCore")


class DigitalEmpireCore:
    def __init__(self):
        for directory in ["logs", "data", "sandbox", "vault"]:
            Path(directory).mkdir(parents=True, exist_ok=True)
        self.is_running = True
        logger.info("Batch 1: Core Architecture Initialized.")
