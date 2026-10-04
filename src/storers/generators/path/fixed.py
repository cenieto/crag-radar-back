from pathlib import Path
from typing import IO, Literal

from registry.registry import Config
from storers.abcs import PathGeneratorAbstract, PathGeneratorConfigAbstract, NamedFile


class BaseFixedPathGeneratorConfig(PathGeneratorConfigAbstract, Config["BaseFixedPathGenerator"]):
    type: Literal["fixed"] = "fixed"
    fixed_path: Path
    

class BaseFixedPathGenerator(PathGeneratorAbstract):
    def __init__(
        self,
        config: BaseFixedPathGeneratorConfig,
    ):
        """Initialize the fixed path generator with a configuration object."""
        self.fixed_path = config.fixed_path
        
    def generate_path(
        self,
        file_object: NamedFile,
    ) -> Path:
        """Generate a fixed path for the given file object."""
        filename: str = Path(file_object.name).name
        full_path = Path(self.fixed_path) / filename
        return full_path