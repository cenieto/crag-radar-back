import datetime
from pathlib import Path
from typing import BinaryIO, TextIO

from store_files.abcs import BasePathGenerator


class DefaultPathGenerator(BasePathGenerator):
    def __init__(
        self,
        base_path: str,
    ):
        """Initialize the default path generator with a base path."""
        self.base_path = base_path
        
    def generate_path(
        self,
        file_object: TextIO | BinaryIO,
    ) -> Path:
        """Generate a default path for the given file object."""

        filename: str = Path(file_object.name).name
        full_path = Path(self.base_path) / filename
        
        return full_path


class DatePathGenerator(BasePathGenerator):
    def __init__(
        self,
        base_path: str,
    ):
        """Initialize the date path generator with a base path."""
        self.base_path = base_path
        
    def generate_path(
        self,
        file_object: TextIO | BinaryIO,
    ) -> Path:
        """Generate a date-based path for the given file object."""

        filename: str = Path(file_object.name).name
        
        date: datetime.date = datetime.date.today()
        date_subdir = date.strftime("%Y/%m/%d")
        
        full_path = Path(self.base_path) / date_subdir / filename
        
        return full_path
