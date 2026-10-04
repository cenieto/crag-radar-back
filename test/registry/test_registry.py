from dataclasses import dataclass

import pytest

from registry.registry import Config, RegistryClass


class Base:
    pass


@dataclass
class ConfigA:
    value: int


@dataclass
class ConfigB:
    name: str


class A(Base):
    def __init__(self, config: ConfigA):
        self.config = config


class B(Base):
    def __init__(self, config: ConfigB):
        self.config = config


@pytest.fixture
def registry():
    class Registry(RegistryClass[Base]):
        pass

    return Registry


def test_set_and_get(registry):
    registry.set(A, ConfigA)
    assert registry.get(ConfigA) is A


def test_generate_builds_object_with_config(registry):
    registry.set(A, ConfigA)
    registry.set(B, ConfigB)
    config = ConfigA(value=3)
    obj = registry.generate(config)
    assert isinstance(obj, A)
    assert obj.config is config
    assert isinstance(registry.generate(ConfigB("x")), B)


def test_get_unregistered_raises_key_error(registry):
    with pytest.raises(KeyError, match="ConfigA"):
        registry.get(ConfigA)


def test_generate_unregistered_raises_key_error(registry):
    with pytest.raises(KeyError):
        registry.generate(ConfigA(1))


def test_set_duplicate_config_raises_value_error(registry):
    registry.set(A, ConfigA)
    with pytest.raises(ValueError, match="already registered"):
        registry.set(B, ConfigA)


def test_set_rejects_non_classes(registry):
    with pytest.raises(TypeError):
        registry.set(A(ConfigA(1)), ConfigA)
    with pytest.raises(TypeError):
        registry.set(A, ConfigA(1))


def test_registries_are_independent():
    class R1(RegistryClass[Base]):
        pass

    class R2(RegistryClass[Base]):
        pass

    R1.set(A, ConfigA)
    with pytest.raises(KeyError):
        R2.get(ConfigA)


def test_base_class_cannot_be_used_directly():
    with pytest.raises(TypeError):
        RegistryClass.set(A, ConfigA)


def test_generate_with_config_marker(registry):
    class Model(Base):
        def __init__(self, config: "ModelConfig"):
            self.config = config

    class ModelConfig(Config[Model]):
        pass

    registry.set(Model, ModelConfig)
    assert isinstance(registry.generate(ModelConfig()), Model)
    