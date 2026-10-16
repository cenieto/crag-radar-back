import pytest
from pydantic import BaseModel

from registry.multiregistry import MultiRegistryClass, register_class


@pytest.fixture(autouse=True)
def _fresh_multi_registry():
    MultiRegistryClass.reset_instance()
    yield
    MultiRegistryClass.reset_instance()


def test_register_class_decorator() -> None:
    class Base:
        def __init__(self, config: object) -> None: ...

    class Config(BaseModel):
        pass

    MultiRegistryClass().create_registry(Base)

    @register_class(Base, Config)
    class Derived(Base):
        def __init__(self, config: Config) -> None:
            super().__init__(config)

    registry = MultiRegistryClass()
    assert registry.get_registry(Base).get(Config) is Derived
