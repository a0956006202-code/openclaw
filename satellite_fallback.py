import logging


logger = logging.getLogger("SatelliteNet")


class SatelliteNetworkFallback:
    def check_terrestrial_connection(self) -> bool:
        terrestrial_down = False
        if terrestrial_down:
            logger.warning(
                "Terrestrial network failure detected! "
                "Switching to Starlink / P2P mesh relay."
            )
            return True
        return False
