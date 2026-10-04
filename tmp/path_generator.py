import datetime
from pathlib import Path
from typing import BinaryIO, TextIO

from pydantic import BaseModel

from tmp.abcs import PathGeneratorAbstract


class DefaultPathGeneratorConfig(BaseModel):
    type: str = "default"
    base_path: Path
    
class DefaultPathGenerator(PathGeneratorAbstract):
    def __init__(
        self,
        base_path: Path,
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


class DatePathGeneratorConfig(BaseModel):
    type: str = "date"
    base_path: Path
    

class DatePathGenerator(PathGeneratorAbstract):
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
