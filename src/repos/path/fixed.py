from pathlib import Path
from typing import Literal

from registry.registry import Config
from repos.abcs import NamedFile, PathGeneratorAbstract, PathGeneratorConfigAbstract


class FixedPathGeneratorConfig(PathGeneratorConfigAbstract, Config["FixedPathGenerator"]):
    type: Literal["fixed"] = "fixed"
    base_path: Path


class FixedPathGenerator(PathGeneratorAbstract):
    def __init__(
        self,
        config: FixedPathGeneratorConfig,
    ):
        """Initialize the fixed path generator with a configuration object."""
        self.base_path: Path = config.base_path

    def generate_path(
        self,
        file_object: NamedFile[str] | NamedFile[bytes],
    ) -> Path:
        """Generate a fixed path for the given file object."""
        filename: str = Path(file_object.name).name
        full_path = Path(self.base_path) / filename
        return full_path
