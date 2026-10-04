from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import IO, Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import field_validator

from registry.registry import Config
from storers.abcs import PathGeneratorAbstract, PathGeneratorConfigAbstract, NamedFile


class DatePathGeneratorConfig(PathGeneratorConfigAbstract, Config["DatePathGenerator"]):
    type: Literal["date"] = "date"
    base_path: Path
    timezone: str = "UTC"

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        """Check that ``value`` is a valid IANA timezone name."""
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError) as e:
            raise ValueError(
                f"Invalid timezone '{value}'. "
                "Use an IANA name such as 'UTC' or 'Europe/Madrid'."
            ) from e
        return value
    
    
class DatePathGenerator(PathGeneratorAbstract):
    def __init__(
        self,
        config: DatePathGeneratorConfig,
    ):
        """Initialize the date path generator with a configuration object."""
        self.base_path = config.base_path
        self.timezone = self._set_timezone(config.timezone)
        
    def _set_timezone(self, timezone_str: str) -> ZoneInfo:
        """Set the timezone for the date path generator."""
        try:
            return ZoneInfo(timezone_str)
        except ZoneInfoNotFoundError as e:
            raise ValueError(
                f"Invalid timezone '{timezone_str}'. "
                "Use an IANA name such as 'UTC' or 'Europe/Madrid'."
            ) from e
        
    def generate_path(
        self,
        file_object: NamedFile,
    ) -> Path:
        """Generate a path based on the current date for the given file object."""
        filename: str = Path(file_object.name).name
        date_today = datetime.now(tz=self.timezone).date()
        date_subdir = date_today.strftime("%Y/%m/%d")
        
        full_path = Path(self.base_path) / date_subdir / filename
        
        return full_path