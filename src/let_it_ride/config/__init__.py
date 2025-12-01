"""Configuration handling.

This module contains configuration loading and validation:
- Pydantic models for all configuration sections
- YAML configuration loader
- Paytable definitions
"""

from let_it_ride.config.loader import (
    ConfigFileNotFoundError,
    ConfigParseError,
    ConfigurationError,
    ConfigValidationError,
    load_config,
    load_config_from_string,
    validate_config,
)
from let_it_ride.config.models import (
    BankrollConfig,
    BonusStrategyConfig,
    DeckConfig,
    FullConfig,
    MetadataConfig,
    OutputConfig,
    PaytablesConfig,
    SimulationConfig,
    StrategyConfig,
)

__all__ = [
    # Loader functions
    "load_config",
    "load_config_from_string",
    "validate_config",
    # Exceptions
    "ConfigurationError",
    "ConfigFileNotFoundError",
    "ConfigParseError",
    "ConfigValidationError",
    # Core models
    "FullConfig",
    "MetadataConfig",
    "SimulationConfig",
    "DeckConfig",
    "BankrollConfig",
    "StrategyConfig",
    "BonusStrategyConfig",
    "PaytablesConfig",
    "OutputConfig",
]
