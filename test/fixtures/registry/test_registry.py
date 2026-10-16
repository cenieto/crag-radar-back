import pytest
from pydantic import BaseModel, ConfigDict, ValidationError


class AConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    alpha: float


class BConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str


class A:
    def __init__(self, config: AConfig) -> None: ...


class B:
    def __init__(self, config: BConfig) -> None: ...


class Reg(RegistryClass[object]):
    pass


def test_get_config_from_dict_selects_matching_config() -> None:
    Reg.set(A, AConfig)
    Reg.set(B, BConfig)
    assert Reg.get_config_from_dict({"alpha": 0.5}) == AConfig(alpha=0.5)
    assert isinstance(Reg.generate(Reg.get_config_from_dict({"name": "x"})), B)


def test_get_config_from_dict_no_match_raises() -> None:
    Reg.set(A, AConfig)
    with pytest.raises(ValidationError):
        Reg.get_config_from_dict({"unknown": 1})


def test_get_config_from_dict_empty_registry_raises() -> None:
    class Empty(RegistryClass[object]):
        pass

    with pytest.raises(LookupError):
        Empty.get_config_from_dict({"alpha": 1})
