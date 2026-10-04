from abc import ABC, abstractmethod
from typing import IO

from pydantic import BaseModel, ConfigDict


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
        config,
    ):
        """Initialize the path generator with a configuration object."""
        self.config = config
        
    @abstractmethod
    def generate_path(
        self, 
        file_object: IO,
    ):
        """Generate a path based on the provided arguments."""
        pass
    