import logging


logger = logging.getLogger("LiquidSovereignty")


class LiquidSovereigntyMigration:
    def export_encrypted_digital_twin(self) -> str:
        logger.info(
            "Packing empire state (code, weights, vault) into an encrypted "
            "digital twin archive..."
        )
        return "empire_digital_twin_backup_encrypted.bin"
