# Racker

`racker` links classes to the pydantic models that configure them. You can then build an
object from a plain dictionary, such as one loaded from a JSON or YAML file, without
knowing its class in advance.

The registry lives in `racker.registry`, and its pydantic integration in
`racker.validators`. The API reference lists every class and method of
[`racker.registry`](reference/racker/registry.md) and
[`racker.validators`](reference/racker/validators.md).

## Concepts

| Term | Meaning |
| --- | --- |
| **Base class** | A family of interchangeable classes, for example `Storage`. Each base class gets its own registry. |
| **Class** | A concrete subclass of the base class, for example `LocalStorage`. Its constructor takes one argument: its config object. |
| **Config class** | A pydantic `BaseModel` that describes the settings of one class, for example `LocalStorageConfig`. |
| **Discriminator** | The `type` field of every config class. Its default value names the config class, and the `type` value of a dictionary selects which config class reads it. The field name is in `Entry.DISCRIMINATOR_FIELD_NAME`. |

`racker.registry` has three classes, each built on the one before:

- [`Entry`][racker.registry.Entry]: one class, its base class and its config class.
- [`RegistryBase`][racker.registry.RegistryBase]: the entries of a single base class.
- [`Registry`][racker.registry.Registry]: one `RegistryBase` per base class.

`racker.validators` has one class:

- [`Registered`][racker.validators.Registered]: a marker for pydantic fields that builds
  their objects from configuration dictionaries through a `Registry`.

## Usage

### 1. Define the classes

```python
from pydantic import BaseModel


class Storage:
    """Base class of every storage."""


class LocalStorageConfig(BaseModel):
    type: str = "local"
    root: str


class LocalStorage(Storage):
    def __init__(self, config: LocalStorageConfig) -> None:
        self.root: str = config.root


class S3StorageConfig(BaseModel):
    type: str = "s3"
    bucket: str


class S3Storage(Storage):
    def __init__(self, config: S3StorageConfig) -> None:
        self.bucket: str = config.bucket
```

Each config class needs a `type` field with a fixed default value. That value must be
different for every config class of the same base class.

### 2. Register them

```python
from racker.registry import Registry

registry: Registry = Registry()
registry.add_base(base_class=Storage)
registry.register(class_=LocalStorage, config_class=LocalStorageConfig, base_class=Storage)
registry.register(class_=S3Storage, config_class=S3StorageConfig, base_class=Storage)
```

`add_base` creates the registry of a base class and returns it. You must add a base class
before registering any of its classes. `register` builds the `Entry`, checks it, stores it
and returns it. If you already have an `Entry`, use `add_entry` instead.

### 3. Build objects from dictionaries

```python
storage: Storage = registry.instantiate_from_dict(
    base_class=Storage,
    config_dict={"type": "s3", "bucket": "climbing-photos"},
)
assert isinstance(storage, S3Storage)
```

`instantiate_from_dict` works in three steps:

1. It reads `config_dict["type"]` (`"s3"`) and picks the config class whose `type`
   default matches (`S3StorageConfig`).
2. It validates the dictionary into that config class. Missing or invalid fields raise
   `pydantic.ValidationError`.
3. It finds the class registered for that config class (`S3Storage`) and returns
   `S3Storage(config)`.

### 4. Look up classes

```python
registry.get_class_by_config_class(config_class=S3StorageConfig)  # S3Storage
registry.get_config_class_by_class(class_=LocalStorage)            # LocalStorageConfig
```

Both methods search the registries of every base class and return `None` when nothing
matches.

### 5. Use registered objects in pydantic models

To let a model field accept a configuration dictionary and hold the built object, use
the [`Registered`][racker.validators.Registered] marker. Declare a generic alias once per
registry, then name the base class in each field:

```python
from typing import Annotated

from pydantic import BaseModel

from racker.registry import BaseT
from racker.validators import Registered

Built = Annotated[BaseT, Registered(registry=registry)]


class AppConfig(BaseModel):
    storage: Built[Storage]
    backup_storage: Built[Storage] | None = None
    mirror_storages: list[Built[Storage]] = []


app_config: AppConfig = AppConfig.model_validate(
    {
        "storage": {"type": "s3", "bucket": "climbing-photos"},
        "mirror_storages": [{"type": "local", "root": "/mirror"}],
    }
)
assert isinstance(app_config.storage, S3Storage)
```

`Built[Storage]` means `Annotated[Storage, Registered(registry)]`:

- **Pydantic** passes `Storage` to the marker, which uses it as the `base_class` of
  `instantiate_from_dict`. Each dictionary in the field is built into an object. Objects
  that are already built are kept, as long as they are instances of `Storage`.
- **Type checkers** ignore the marker and see `storage` as a `Storage`,
  `backup_storage` as `Storage | None`, and `mirror_storages` as `list[Storage]`.

The model needs neither `arbitrary_types_allowed` nor a validator. The registry is read
when data is validated, so classes can be registered after the model is defined.
`Registered` also works with `TypeAdapter` and pydantic dataclasses.

!!! note "Declare the alias at module level"
    Write `Built = Annotated[BaseT, Registered(registry=registry)]` directly. Type
    checkers only recognise an alias written as `Annotated[...]`, not one returned by a
    function.

!!! note "Passing dictionaries to the constructor"
    `AppConfig(storage={...})` works at runtime, but type checkers expect a `Storage`
    there. Use `AppConfig.model_validate(data)` for raw data, or enable pydantic's mypy
    plugin (`plugins = ["pydantic.mypy"]` under `[tool.mypy]`), which accepts any value
    in the constructor.

`Registered` only annotates a class. Use it inside other types, as in
`list[Built[Storage]]`, rather than around them: `Annotated[list[Storage], Registered(...)]`
raises `TypeError` when the model is defined.

Validating a `Registered` field fails with `pydantic.ValidationError`, naming the field,
when:

- the value is neither a dictionary nor an instance of the base class;
- the base class was never added to the registry;
- the dictionary has no `type`, or a `type` no registered config class uses;
- the dictionary does not satisfy the selected config class.

Two pydantic features don't support `Registered` fields:

- `model_json_schema()` raises `PydanticInvalidForJsonSchema`, because pydantic can't
  describe an instance check in JSON Schema.
- `model_dump()` returns the built object, not its configuration dictionary.

## Rules

Racker checks the following rules when an entry is created or registered. Each broken
rule raises an error and leaves the registry unchanged.

| Rule | Checked by | Error |
| --- | --- | --- |
| The class is a subclass of the base class. | `Entry` | `ValueError` |
| The config class has a `type` field. | `Entry` | `ValueError` |
| The `type` field has a fixed default value: not required, not set with `default_factory`, and not `None`. | `Entry` | `ValueError` |
| The entry has the base class of its registry. | `RegistryBase.register` | `ValueError` |
| The config class is not registered yet. | `RegistryBase.register` | `ValueError` |
| The class is not registered yet. | `RegistryBase.register` | `ValueError` |
| No other config class of the same base class uses the same `type` value. | `RegistryBase.register` | `ValueError` |
| The config class and the class are not registered under another base class. | `Registry.add_entry` | `ValueError` |
| The base class has been added with `add_base`. | `Registry.add_entry` | `KeyError` |

These rules make the link between classes and config classes one-to-one across the whole
`Registry`. A dictionary always leads to exactly one class, and a lookup in either
direction always has at most one answer.

!!! note
    `Entry` is a pydantic model, so the errors it raises reach the caller as
    `pydantic.ValidationError`. That error is a subclass of `ValueError`, so
    `except ValueError` catches every rule in the table except the last one.

## Errors when building objects

| Situation | Error |
| --- | --- |
| The base class was never added. | `KeyError` |
| The base class was added but has no entries. | `ValueError` |
| The dictionary has no `type`, or a `type` no registered config class uses. | `pydantic.ValidationError` |
| The dictionary does not satisfy the selected config class. | `pydantic.ValidationError` |

## Typing

`Entry` and `RegistryBase` are generic over their base class, and type checkers infer it
from the `base_class` argument:

```python
storage_registry = registry.add_base(base_class=Storage)  # RegistryBase[Storage]
storage_registry.classes_                                  # list[type[Storage]]
storage_registry.config_classes                            # list[type[BaseModel]]
registry.instantiate_from_dict(base_class=Storage, config_dict={...})  # Storage
```

`Registry.get_class_by_config_class` returns a plain `type`, because it searches every
base class and so can't know which one the result belongs to.

## Design notes

- **No global state.** Each `Registry()` is independent, so tests and different parts of
  an application can each use their own.
- **Adapter built on registration.** `RegistryBase.config_type_adapter` is a pydantic
  `TypeAdapter` over all the config classes of the base class. It is rebuilt each time an
  entry is registered and reused for every `instantiate_from_dict` call in between.
- **Tagged union without `Literal`.** pydantic's usual discriminated unions need the
  `type` field to be a `Literal`. Racker instead tags each config class with the default
  value of its `type` field. Config classes can declare `type: str = "local"`, and the
  dictionary still selects the right class.
