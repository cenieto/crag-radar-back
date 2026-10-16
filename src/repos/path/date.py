from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import field_validator

from registry.registry import Config
from repos.abcs import NamedFile, PathGeneratorAbstract, PathGeneratorConfigAbstract


class DatePathGeneratorConfig(PathGeneratorConfigAbstract, Config["DatePathGenerator"]):
    type: Literal["date"] = "date"
    base_path: Path
    timezone: str = "UTC"

    @field_validator("timezone", mode="after")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        """Check that ``value`` is a valid IANA timezone name."""
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError) as e:
            raise ValueError(
                f"Invalid timezone '{value}'. Use an IANA name such as 'UTC' or 'Europe/Madrid'."
            ) from e
        return value

    @property
    def tzinfo(self) -> ZoneInfo:
        return ZoneInfo(self.timezone)


class DatePathGenerator(PathGeneratorAbstract):
    def __init__(
        self,
        config: DatePathGeneratorConfig,
    ):
        """Initialize the date path generator with a configuration object."""
        self.base_path = config.base_path
        self.tzinfo = config.tzinfo

    def generate_path(
        self,
        file_object: NamedFile[str] | NamedFile[bytes],
    ) -> Path:
        """Generate a path based on the current date for the given file object."""
        filename: str = Path(file_object.name).name
        date_today = datetime.now(tz=self.tzinfo).date()
        date_subdir = date_today.strftime("%Y/%m/%d")

        full_path = Path(self.base_path) / date_subdir / filename

        return full_path
