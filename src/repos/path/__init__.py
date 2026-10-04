
from typing import Annotated, Union, Literal

from pydantic import Field, TypeAdapter

from registry.registry import RegistryClass
from repos.abcs import PathGeneratorAbstract
from repos.path.date import DatePathGenerator, DatePathGeneratorConfig
from repos.path.fixed import FixedPathGenerator, FixedPathGeneratorConfig


PathGeneratorConfig = Annotated[
    Union[DatePathGeneratorConfig, FixedPathGeneratorConfig],
    Field(discriminator="type"),
]

path_generator_adapter: TypeAdapter[PathGeneratorConfig] = TypeAdapter(PathGeneratorConfig)

class PathGeneratorRegistry(RegistryClass[PathGeneratorAbstract]):
    ...
    

path_generator_registry = PathGeneratorRegistry()

path_generator_registry.set(DatePathGenerator, DatePathGeneratorConfig)
path_generator_registry.set(FixedPathGenerator, FixedPathGeneratorConfig)

