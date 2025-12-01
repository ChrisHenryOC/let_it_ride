"""Configuration loader for Let It Ride simulator.

This module provides functions to load and validate YAML configuration files.
It uses Pydantic models for validation and provides descriptive error messages.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import yaml
from pydantic import ValidationError

from let_it_ride.config.models import FullConfig

if TYPE_CHECKING:
    from typing import Any


class ConfigurationError(Exception):
    """Base exception for configuration errors.

    Attributes:
        message: Human-readable error description.
        details: Additional error details (e.g., validation errors).
    """

    def __init__(self, message: str, details: str | None = None) -> None:
        """Initialize configuration error.

        Args:
            message: Human-readable error description.
            details: Additional error details.
        """
        super().__init__(message)
        self.message = message
        self.details = details

    def __str__(self) -> str:
        """Return string representation of the error."""
        if self.details:
            return f"{self.message}\n\nDetails:\n{self.details}"
        return self.message


class ConfigFileNotFoundError(ConfigurationError):
    """Raised when the configuration file does not exist."""


class ConfigParseError(ConfigurationError):
    """Raised when the YAML file cannot be parsed."""


class ConfigValidationError(ConfigurationError):
    """Raised when the configuration fails Pydantic validation."""


def _format_validation_errors(error: ValidationError) -> str:
    """Format Pydantic validation errors into a readable string.

    Args:
        error: The Pydantic ValidationError.

    Returns:
        A formatted string describing all validation errors.
    """
    lines = []
    for err in error.errors():
        location = ".".join(str(loc) for loc in err["loc"])
        msg = err["msg"]
        err_type = err["type"]

        if location:
            lines.append(f"  - {location}: {msg} ({err_type})")
        else:
            lines.append(f"  - {msg} ({err_type})")

    return "\n".join(lines)


def load_config(path: Path | str) -> FullConfig:
    """Load and validate a configuration file.

    This function reads a YAML configuration file, parses it, and validates
    it against the FullConfig Pydantic model. Any missing optional fields
    are filled with their default values.

    Args:
        path: Path to the YAML configuration file.

    Returns:
        A validated FullConfig object with all fields populated.

    Raises:
        ConfigFileNotFoundError: If the file does not exist.
        ConfigParseError: If the YAML is invalid.
        ConfigValidationError: If the configuration fails validation.

    Example:
        >>> config = load_config("configs/sample_config.yaml")
        >>> print(config.simulation.num_sessions)
        10000
    """
    # Convert to Path if string
    config_path = Path(path) if isinstance(path, str) else path

    # Check file exists
    if not config_path.exists():
        raise ConfigFileNotFoundError(
            f"Configuration file not found: {config_path}",
            details=f"Please ensure the file exists at: {config_path.absolute()}",
        )

    if not config_path.is_file():
        raise ConfigFileNotFoundError(
            f"Path is not a file: {config_path}",
            details="The path must point to a YAML file, not a directory.",
        )

    # Read and parse YAML
    try:
        content = config_path.read_text(encoding="utf-8")
    except OSError as e:
        raise ConfigParseError(
            f"Cannot read configuration file: {config_path}",
            details=str(e),
        ) from e

    try:
        data: dict[str, Any] | None = yaml.safe_load(content)
    except yaml.YAMLError as e:
        raise ConfigParseError(
            f"Invalid YAML in configuration file: {config_path}",
            details=str(e),
        ) from e

    # Handle empty file
    if data is None:
        data = {}

    # Validate against Pydantic model
    try:
        config = FullConfig.model_validate(data)
    except ValidationError as e:
        raise ConfigValidationError(
            f"Configuration validation failed: {config_path}",
            details=_format_validation_errors(e),
        ) from e

    return config


def load_config_from_string(content: str) -> FullConfig:
    """Load and validate a configuration from a YAML string.

    This is useful for testing or for configurations stored in
    databases or other non-file sources.

    Args:
        content: YAML configuration string.

    Returns:
        A validated FullConfig object with all fields populated.

    Raises:
        ConfigParseError: If the YAML is invalid.
        ConfigValidationError: If the configuration fails validation.

    Example:
        >>> yaml_content = '''
        ... simulation:
        ...   num_sessions: 1000
        ... '''
        >>> config = load_config_from_string(yaml_content)
        >>> print(config.simulation.num_sessions)
        1000
    """
    try:
        data: dict[str, Any] | None = yaml.safe_load(content)
    except yaml.YAMLError as e:
        raise ConfigParseError(
            "Invalid YAML content",
            details=str(e),
        ) from e

    # Handle empty string
    if data is None:
        data = {}

    try:
        config = FullConfig.model_validate(data)
    except ValidationError as e:
        raise ConfigValidationError(
            "Configuration validation failed",
            details=_format_validation_errors(e),
        ) from e

    return config


def validate_config(data: dict[str, Any]) -> FullConfig:
    """Validate a configuration dictionary.

    This is useful for validating configurations that have already been
    parsed from YAML or constructed programmatically.

    Args:
        data: Configuration dictionary.

    Returns:
        A validated FullConfig object with all fields populated.

    Raises:
        ConfigValidationError: If the configuration fails validation.

    Example:
        >>> data = {"simulation": {"num_sessions": 1000}}
        >>> config = validate_config(data)
        >>> print(config.simulation.num_sessions)
        1000
    """
    try:
        config = FullConfig.model_validate(data)
    except ValidationError as e:
        raise ConfigValidationError(
            "Configuration validation failed",
            details=_format_validation_errors(e),
        ) from e

    return config
