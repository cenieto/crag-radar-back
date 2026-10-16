from abc import ABC, abstractmethod
from pathlib import Path
from typing import Protocol, TypeVar

from pydantic import BaseModel, ConfigDict

T_co = TypeVar("T_co", str, bytes, covariant=True)


class NamedFile(Protocol[T_co]):
    @property
    def name(self) -> str: ...

    def read(self, size: int = -1, /) -> T_co: ...


class BaseConfig(BaseModel):
    """Base configuration class for path generators."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )


class PathGeneratorConfigAbstract(BaseConfig):
    """Initialize the base path generator configuration with a type identifier."""

    type: str = "base"


class PathGeneratorAbstract(ABC):
    def __init__(
        self,
        config: PathGeneratorConfigAbstract,
    ):
        """Initialize the path generator with a configuration object."""
        self.config = config

    @abstractmethod
    def generate_path(
        self,
        file_object: NamedFile[str] | NamedFile[bytes],
    ) -> Path:
        """Generate a path based on the provided arguments."""
        pass


class RepositoryConfigAbstract(BaseConfig):
    """Base configuration class for repository objects."""

    type: str = "base"


class RepositoryAbstract(ABC):
    def __init__(
        self,
        config: RepositoryConfigAbstract,
    ):
        """Initialize the repository with a configuration object."""
        self.config = config

    @abstractmethod
    def save(
        self,
        file_object: NamedFile[str] | NamedFile[bytes],
    ) -> bool:
        """Save a file to the repository based on the provided arguments."""
        pass
