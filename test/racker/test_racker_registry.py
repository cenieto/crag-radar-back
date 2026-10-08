import pytest

from pydantic import BaseModel
from racker.registry import Entry, RegistryBase


class Base:
    pass


class Sub(Base):
    pass


class Config(BaseModel):
    type: str = "example"
    pass


class SubB(Base):
    pass


class ConfigB(BaseModel):
    type: str = "example_b"
    pass


class OtherBase: ...


class OtherClass(OtherBase): ...


class OtherConfig(BaseModel):
    type: str = "other_example"
    pass


def test_entry_validation():

    # Valid entry
    entry = Entry(base_class=Base, class_=Sub, config_class=Config)
    assert entry.base_class == Base
    assert entry.class_ == Sub
    assert entry.config_class == Config

    # Invalid entry: class_ is not a subclass of base_class
    with pytest.raises(
        ValueError,
        match=r"is not a subclass of",
    ):
        Entry(base_class=Base, class_=int, config_class=Config)

    # Invalid entry: config_class has no discriminator field
    class InvalidConfig(BaseModel):
        pass

    with pytest.raises(
        ValueError,
        match=rf"{InvalidConfig} has no discriminator field: '{Entry._discriminator}'",
    ):
        Entry(base_class=Base, class_=Sub, config_class=InvalidConfig)


def test_RegistryBase_validation():
    registry_base: RegistryBase = RegistryBase(
        base_class=Base,
    )

    entry_1: Entry = Entry(
        base_class=Base,
        class_=Sub,
        config_class=Config,
    )

    registry_base.register(
        entry=entry_1,
    )

    entry_2: Entry = Entry(
        base_class=Base,
        class_=SubB,
        config_class=ConfigB,
    )

    registry_base.register(
        entry=entry_2,
    )

    entry_3: Entry = Entry(
        base_class=OtherBase,
        class_=OtherClass,
        config_class=OtherConfig,
    )

    assert registry_base.config_classes == [Config, ConfigB]
    assert registry_base.classes_ == [Sub, SubB]

    assert registry_base.is_entry_registered(entry=entry_1)
    assert registry_base.is_entry_registered(entry=entry_2)
    assert not registry_base.is_entry_registered(entry=entry_3)

    assert registry_base.get_entry_from_class_(Sub) == entry_1
    assert registry_base.get_entry_from_class_(SubB) == entry_2

    assert registry_base.get_entry_from_config_class(Config) == entry_1
    assert registry_base.get_entry_from_config_class(ConfigB) == entry_2

    with pytest.raises(
        ValueError,
        match=r"Entry for .*? already registered",
    ):
        registry_base.register(
            entry=entry_2,
        )

    with pytest.raises(
        ValueError,
        match=r"Entry for .*? already registered",
    ):
        registry_base._check_entry_for_register(
            entry=entry_2,
        )

    assert not registry_base.is_entry_of_base_type(
        entry=entry_3,
    )
    with pytest.raises(
        ValueError,
        match=r"Entry for .*? is not of base class: ",
    ):
        registry_base._check_entry_for_register(
            entry=entry_3,
        )
