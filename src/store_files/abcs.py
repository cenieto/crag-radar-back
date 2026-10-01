from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO, TextIO


class BasePathGenerator(ABC):
    @abstractmethod
    def generate_path(
        self,
        file_object: TextIO | BinaryIO,
    ) -> Path:
        """Generate a path for the given file object."""
        pass


class BaseStore(ABC):
    @abstractmethod
    def __init__(
        self,        
        path_generator: BasePathGenerator,
    ):
        """Initialize the store with a path generator."""
        self.path_generator = path_generator

    @abstractmethod
    def save(
        self,
        file_object: TextIO | BinaryIO,
    ) -> Path:
        """Save the file object to the given path.

        Returns the path where the file object was saved.
        """
        pass
    
    