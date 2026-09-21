import logging


logger = logging.getLogger("TaxCompliance")


class DynamicTaxRouter:
    def calculate_and_route_tax(self, revenue: float, jurisdiction: str) -> float:
        tax_rates = {"US": 0.21, "EU": 0.19, "SG": 0.17}
        rate = tax_rates.get(jurisdiction, 0.20)
        tax_reserve = revenue * rate
        logger.info(
            f"Jurisdiction [{jurisdiction}]: Reserved "
            f"{tax_reserve} for automated tax compliance."
        )
        return tax_reserve
