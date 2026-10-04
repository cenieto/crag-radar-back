from pathlib import Path

from repos.path import path_generator_registry, path_generator_adapter
from repos.path.date import DatePathGenerator, DatePathGeneratorConfig
from repos.path.fixed import FixedPathGenerator, FixedPathGeneratorConfig


def test_path_generator_registry() -> None:
    assert path_generator_registry.get(DatePathGeneratorConfig) is DatePathGenerator
    assert path_generator_registry.get(FixedPathGeneratorConfig) is FixedPathGenerator


def test_path_generator_config_adapter() -> None:
    config_data = {"type": "date", "base_path": "/data"}
    config: DatePathGeneratorConfig = path_generator_adapter.validate_python(config_data)
    assert isinstance(config, DatePathGeneratorConfig)
    assert config.base_path == Path("/data")
    
    config_data = {"type": "fixed", "base_path": "/data"}
    config: FixedPathGeneratorConfig = path_generator_adapter.validate_python(config_data)
    assert isinstance(config, FixedPathGeneratorConfig)
    assert config.base_path == Path("/data")
