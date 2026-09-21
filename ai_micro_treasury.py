import logging


logger = logging.getLogger("MicroTreasury")


class ProgrammableMicroTreasury:
    def __init__(self, balance: float):
        self.balance = balance

    def authorize_agent_spend(
        self,
        agent_id: str,
        amount: float,
        expected_roi: float,
    ) -> bool:
        if expected_roi > 1.5 and self.balance >= amount:
            self.balance -= amount
            logger.info(
                f"Agent [{agent_id}] authorized to spend {amount}. "
                f"New treasury balance: {self.balance}"
            )
            return True
        logger.warning(
            f"Agent [{agent_id}] spend request denied. "
            "Insufficient ROI or balance."
        )
        return False
