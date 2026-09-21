import logging


logger = logging.getLogger("DarwinPruning")


class DarwinianPruningProtocol:
    def evaluate_and_purge_agents(self, agent_metrics: dict):
        for agent_id, roi in agent_metrics.items():
            if roi < 1.0:
                logger.warning(
                    f"Darwinian Trial: Agent [{agent_id}] failed efficiency "
                    f"threshold (ROI: {roi}). Purged."
                )
