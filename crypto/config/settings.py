]"""
Configuration settings for the Wallet Scanner Simulator
"""

import os
from dataclasses import dataclass
from typing import Dict, List


@dataclass
class Settings:
    """Main configuration class"""

    # Address generation
    NUM_ADDRESSES: int = 10000
    ADDRESS_TYPES: List[str] = None
    ACTIVE_PROBABILITY: float = 0.001  # 0.1% chance of finding active wallet
    RICH_PROBABILITY: float = 0.0001  # 0.01% chance of finding rich wallet

    # Scanning
    MAX_WORKERS: int = 8
    BATCH_SIZE: int = 100
    SCAN_DELAY: float = 0.001  # seconds per address scan
    RETRY_ATTEMPTS: int = 3

    # Simulation
    SIMULATION_SPEED: float = 1.0  # multiplier for simulation speed
    ENABLE_RANDOM_ERRORS: bool = True
    ERROR_PROBABILITY: float = 0.001

    # Output
    UPDATE_INTERVAL: float = 0.5  # seconds between UI updates
    LOG_LEVEL: str = "INFO"
    COLOR_OUTPUT: bool = True

    # Address format probabilities
    ADDRESS_FORMATS: Dict[str, float] = None

    def __post_init__(self):
        if self.ADDRESS_TYPES is None:
            self.ADDRESS_TYPES = ["ethereum", "bitcoin", "solana", "ripple", "cardano"]

        if self.ADDRESS_FORMATS is None:
            self.ADDRESS_FORMATS = {
                "ethereum": 0.4,  # 40% Ethereum addresses
                "bitcoin": 0.3,  # 30% Bitcoin addresses
                "solana": 0.15,  # 15% Solana addresses
                "ripple": 0.1,  # 10% Ripple addresses
                "cardano": 0.05,  # 5% Cardano addresses
            }

    @property
    def address_count(self) -> int:
        """Get number of addresses to generate"""
        return self.NUM_ADDRESSES

    @property
    def worker_count(self) -> int:
        """Get number of worker threads"""
        return min(self.MAX_WORKERS, os.cpu_count() or 4)


# Global settings instance
settings = Settings()