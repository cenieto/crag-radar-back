from __future__ import annotations

import logging
from pathlib import Path
from typing import BinaryIO, TextIO

from tmp.abcs import BaseStore, PathGeneratorAbstract

logger: logging.Logger = logging.getLogger(__name__)


class LocalStore(BaseStore):
    def __init__(
        self,
        path_generator: PathGeneratorAbstract,
    ):
        """Initialize the local store with a path generator."""
        super().__init__(path_generator=path_generator)

    def save(
        self,
        file_object: TextIO | BinaryIO,
    ) -> Path:
        """Save the file object to the given path.

        Returns the path where the file object was saved.       
        """
        try:
            path: Path = self.path_generator.generate_path(file_object)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            content = file_object.read()
            
            if not isinstance(content, (str, bytes)):
                raise TypeError("Unsupported file content type")
            
            if isinstance(content, str):
                path.write_text(content)
            elif isinstance(content, bytes):
                path.write_bytes(content)

            logger.info(f"File saved successfully: {path}")
            return path
        
        except Exception as e:
            logger.error(f"Error saving file: {e}")
            return False