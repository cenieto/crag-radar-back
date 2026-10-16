import logging
from pathlib import Path
from typing import Literal

from registry.registry import Config
from repos.abcs import (
    NamedFile,
    PathGeneratorAbstract,
    RepositoryAbstract,
    RepositoryConfigAbstract,
)

logger: logging.Logger = logging.getLogger(__name__)


class LocalRepositoryConfig(RepositoryConfigAbstract, Config["LocalRepository"]):
    type: Literal["local"] = "local"
    path_generator: PathGeneratorAbstract


class LocalRepository(RepositoryAbstract):
    def __init__(
        self,
        config: LocalRepositoryConfig,
    ):
        """Initialize the local repository with a configuration object."""
        self.path_generator: PathGeneratorAbstract = config.path_generator

    def save(
        self,
        file_object: NamedFile[str] | NamedFile[bytes],
    ) -> bool:
        """Save the file object to the given path.

        Returns the path where the file object was saved.
        """
        try:
            path: Path = self.path_generator.generate_path(file_object)
            path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            content: str | bytes = self._read_content(file_object)
            self._write_content(
                path=path,
                content=content,
            )
            logger.info(f"File saved successfully: {path}")
            return True

        except Exception as e:
            logger.error(f"Error saving file: {e}")
            return False

    def _read_content(
        self,
        file_object: NamedFile[str] | NamedFile[bytes],
    ) -> str | bytes:
        """Read the content of the file object."""
        content = file_object.read()

        if not isinstance(content, (str, bytes)):
            raise TypeError("Unsupported file content type")

        return content

    def _write_content(
        self,
        path: Path,
        content: str | bytes,
    ) -> None:
        """Write content to the path."""
        if isinstance(content, str):
            path.write_text(content)
        elif isinstance(content, bytes):
            path.write_bytes(content)
