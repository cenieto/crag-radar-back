"""Registry that associates classes with the pydantic config classes that describe them."""

from collections.abc import Callable
from typing import Annotated, Any, ClassVar, Generic, TypeVar, Union, cast

from pydantic import BaseModel, Discriminator, Tag, TypeAdapter, model_validator
from pydantic.fields import FieldInfo

BaseT = TypeVar("BaseT")
"""Base class of the objects a registry builds."""


class Entry(BaseModel, Generic[BaseT]):
    """Association between a class, its base class and its pydantic config class.

    The entry is generic over ``BaseT``, the base class, so the type of ``class_``
    is known to type checkers as ``type[BaseT]``.

    Attributes:
        base_class: Base class that ``class_`` must derive from.
        class_: Concrete class being registered.
        config_class: Pydantic model describing the configuration of ``class_``.
            It must declare the discriminator field with a default value.
    """

    _discriminator: ClassVar[str] = "type"

    base_class: type[BaseT]
    class_: type[BaseT]
    config_class: type[BaseModel]

    @model_validator(mode="after")
    def validate_entry(self) -> "Entry[BaseT]":
        """Validate that the classes of the entry are consistent.

        Returns:
            Entry[BaseT]: The validated entry itself.

        Raises:
            ValueError: If ``class_`` is not a subclass of ``base_class``, if
                ``config_class`` has no discriminator field, or if the
                discriminator field has no default value.
        """
        if not issubclass(self.class_, self.base_class):
            raise ValueError(f"{self.class_} is not a subclass of {self.base_class}")

        discriminator_field_name: str = self._discriminator
        config_fields: dict[str, FieldInfo] = self.config_class.model_fields

        if discriminator_field_name not in config_fields:
            raise ValueError(
                f"{self.config_class} has no discriminator field: {discriminator_field_name!r}"
            )

        discriminator_field: FieldInfo = config_fields[discriminator_field_name]
        if discriminator_field.is_required():
            raise ValueError(
                f"{self.config_class} discriminator field {discriminator_field_name!r} "
                "must define a default value"
            )

        return self


class RegistryBase(Generic[BaseT]):
    """Registry of entries that share the same base class and have unique config classes.

    The registry is generic over ``BaseT``, its base class, which is inferred from
    the ``base_class`` given at construction. Returned classes are typed as
    ``type[BaseT]`` and returned config classes as ``type[BaseModel]``.
    """

    def __init__(
        self,
        base_class: type[BaseT],
    ) -> None:
        """Create an empty registry.

        Args:
            base_class: Base class that every registered entry must share.
        """
        self._base_class: type[BaseT] = base_class
        self._entries: dict[type[BaseModel], Entry[BaseT]] = {}

    @property
    def base_class(
        self,
    ) -> type[BaseT]:
        """Return the base class shared by every registered entry.

        Returns:
            type[BaseT]: The registry base class.
        """
        return self._base_class

    @property
    def config_classes(
        self,
    ) -> list[type[BaseModel]]:
        """Return the registered config classes in registration order.

        Returns:
            list[type[BaseModel]]: The config classes of every registered entry.
        """
        return list(self._entries.keys())

    @property
    def classes_(
        self,
    ) -> list[type[BaseT]]:
        """Return the registered classes in registration order.

        Returns:
            list[type[BaseT]]: The classes of every registered entry.
        """
        return [entry.class_ for entry in self._entries.values()]

    @property
    def config_type_adapter(
        self,
    ) -> TypeAdapter[BaseModel]:
        """Return a type adapter that validates data into any registered config class.

        The adapter is a tagged union of every registered config class. The tag of
        each config class is the default value of its discriminator field, and the
        input data selects the config class through the value of that same field.

        Returns:
            TypeAdapter[BaseModel]: Adapter over the union of the registered config classes.

        Raises:
            ValueError: If the registry has no entries.
        """
        has_no_entries: bool = len(self._entries) == 0
        if has_no_entries:
            raise ValueError(f"Registry for {self._base_class} has no entries")

        tagged_config_classes: tuple[Any, ...] = tuple(
            Annotated[
                config_class,
                Tag(self._get_discriminator_value_of_config_class(config_class)),
            ]
            for config_class in self._entries
        )
        config_classes_union: Any = Annotated[
            Union[tagged_config_classes],  # noqa: UP007  (a tuple cannot be joined with ``|``)
            Discriminator(self._get_discriminator_value_of_data),
        ]
        return TypeAdapter(config_classes_union)

    @staticmethod
    def _get_discriminator_value_of_config_class(
        config_class: type[BaseModel],
    ) -> str:
        """Get the default discriminator value of a config class as a tag.

        Args:
            config_class: Config class whose discriminator default is read.

        Returns:
            str: The default value of the discriminator field, as a string.
        """
        discriminator_field: FieldInfo = config_class.model_fields[Entry._discriminator]
        return str(discriminator_field.default)

    @staticmethod
    def _get_discriminator_value_of_data(
        data: Any,
    ) -> str | None:
        """Get the discriminator value of data being validated as a config.

        Args:
            data: Raw dictionary or config instance being validated.

        Returns:
            str | None: The discriminator value as a string, or ``None`` if missing.
        """
        is_raw_dictionary: bool = isinstance(data, dict)
        discriminator_value: Any = (
            data.get(Entry._discriminator)
            if is_raw_dictionary
            else getattr(data, Entry._discriminator, None)
        )
        is_discriminator_missing: bool = discriminator_value is None
        return None if is_discriminator_missing else str(discriminator_value)

    def is_entry_registered(
        self,
        entry: Entry[Any],
    ) -> bool:
        """Tell whether an entry is already registered.

        Args:
            entry: Entry to look for.

        Returns:
            bool: ``True`` if the entry is registered, ``False`` otherwise.
        """
        return entry in self._entries.values()

    def is_config_class_registered(
        self,
        config_class: type[BaseModel],
    ) -> bool:
        """Tell whether a config class is already registered.

        Args:
            config_class: Config class to look for.

        Returns:
            bool: ``True`` if an entry is registered under ``config_class``.
        """
        return config_class in self._entries

    def is_entry_of_base_type(
        self,
        entry: Entry[Any],
    ) -> bool:
        """Tell whether an entry has the same base class as the registry.

        Args:
            entry: Entry to check.

        Returns:
            bool: ``True`` if the entry base class equals the registry base class.
        """
        return entry.base_class == self._base_class

    def _check_entry_for_register(
        self,
        entry: Entry[BaseT],
    ) -> None:
        """Check that an entry can be registered.

        Args:
            entry: Entry to check.

        Raises:
            ValueError: If the entry is already registered, if its base class
                differs from the registry base class, if its config class is
                already registered for another class, or if its discriminator
                value is already used by another config class.
        """
        is_already_registered: bool = self.is_entry_registered(
            entry=entry,
        )
        if is_already_registered:
            raise ValueError(f"Entry for {entry.class_} already registered")

        is_of_registry_base_type: bool = self.is_entry_of_base_type(
            entry=entry,
        )
        if not is_of_registry_base_type:
            raise ValueError(f"Entry for {entry.class_} is not of base class: {self._base_class}")

        is_config_class_taken: bool = self.is_config_class_registered(
            config_class=entry.config_class,
        )
        if is_config_class_taken:
            conflicting_class: type = self._entries[entry.config_class].class_
            raise ValueError(
                f"Config class {entry.config_class} already registered for {conflicting_class}"
            )

        discriminator_value: str = self._get_discriminator_value_of_config_class(entry.config_class)
        registered_config_class: type[BaseModel]
        for registered_config_class in self.config_classes:
            is_discriminator_value_taken: bool = (
                self._get_discriminator_value_of_config_class(registered_config_class)
                == discriminator_value
            )
            if is_discriminator_value_taken:
                raise ValueError(
                    f"Discriminator value {discriminator_value!r} of {entry.config_class} "
                    f"already used by {registered_config_class}"
                )

    def register(
        self,
        entry: Entry[BaseT],
    ) -> None:
        """Register an entry under its config class.

        Args:
            entry: Entry to register.

        Raises:
            ValueError: If the entry cannot be registered (see
                ``_check_entry_for_register``).
        """
        self._check_entry_for_register(
            entry=entry,
        )
        self._entries[entry.config_class] = entry

    def get_entry_from_config_class(
        self,
        config_class: type[BaseModel],
    ) -> Entry[BaseT] | None:
        """Get the entry registered for a config class.

        Args:
            config_class: Config class used as lookup key.

        Returns:
            Entry[BaseT] | None: The matching entry, or ``None`` if the config class
                is not registered.
        """
        return self._entries.get(config_class)

    def get_entry_of_type(
        self,
        class_: type,
    ) -> Entry[BaseT] | None:
        """Get the entry registered for a class.

        Args:
            class_: Class to look for.

        Returns:
            Entry[BaseT] | None: The matching entry, or ``None`` if the class is not registered.
        """
        registered_entry: Entry[BaseT]
        for registered_entry in self._entries.values():
            is_matching_class: bool = class_ == registered_entry.class_
            if is_matching_class:
                return registered_entry
        return None


class Registry:
    """Store one ``RegistryBase`` per base class and resolve classes across all of them."""

    def __init__(
        self,
    ) -> None:
        """Create a registry with no base classes."""
        self._registries: dict[type, RegistryBase[Any]] = {}

    @property
    def registry_bases(
        self,
    ) -> list[RegistryBase[Any]]:
        """Return the stored registries in the order their base classes were added.

        Returns:
            list[RegistryBase[Any]]: The registry of every added base class.
        """
        return list(self._registries.values())

    def is_base_class_registered(
        self,
        base_class: type,
    ) -> bool:
        """Tell whether a registry exists for a base class.

        Args:
            base_class: Base class to look for.

        Returns:
            bool: ``True`` if ``base_class`` has a registry, ``False`` otherwise.
        """
        return base_class in self._registries

    def add_base(
        self,
        base_class: type[BaseT],
    ) -> None:
        """Create and store an empty registry for a base class.

        Args:
            base_class: Base class the new registry manages.

        Raises:
            ValueError: If a registry for ``base_class`` already exists.
        """
        is_base_class_registered: bool = self.is_base_class_registered(
            base_class=base_class,
        )
        if is_base_class_registered:
            raise ValueError(f"Registry for {base_class} already registered")
        registry_base: RegistryBase[BaseT] = RegistryBase(base_class=base_class)
        self._registries[base_class] = registry_base

    def add_entry(
        self,
        entry: Entry[BaseT],
    ) -> None:
        """Register an entry in the registry of its base class.

        Args:
            entry: Entry to register.

        Raises:
            KeyError: If no registry exists for ``entry.base_class``.
            ValueError: If the entry cannot be registered (see ``RegistryBase.register``).
        """
        registry_base: RegistryBase[BaseT] = self._get_registry_base(
            base_class=entry.base_class,
        )
        registry_base.register(
            entry=entry,
        )

    def register(
        self,
        class_: type[BaseT],
        config_class: type[BaseModel],
        base_class: type[BaseT],
    ) -> None:
        """Register a class and its config class in the registry of its base class.

        Args:
            class_: Concrete class being registered.
            config_class: Pydantic model describing the configuration of ``class_``.
            base_class: Base class whose registry receives the entry.

        Raises:
            pydantic.ValidationError: If the classes do not form a valid ``Entry``.
            KeyError: If no registry exists for ``base_class``.
            ValueError: If the entry cannot be registered (see ``RegistryBase.register``).
        """
        entry: Entry[BaseT] = Entry(
            base_class=base_class,
            class_=class_,
            config_class=config_class,
        )
        self.add_entry(
            entry=entry,
        )

    def _get_registry_base(
        self,
        base_class: type[BaseT],
    ) -> RegistryBase[BaseT]:
        """Get the registry that manages a base class.

        Args:
            base_class: Base class whose registry is requested.

        Returns:
            RegistryBase[BaseT]: The registry of ``base_class``.

        Raises:
            KeyError: If no registry exists for ``base_class``.
        """
        is_base_class_registered: bool = self.is_base_class_registered(
            base_class=base_class,
        )
        if not is_base_class_registered:
            raise KeyError(f"No registry for {base_class}")
        return self._registries[base_class]

    def get_class_by_config_class(
        self,
        config_class: type[BaseModel],
    ) -> type | None:
        """Get the class associated with a config class, searching every registry.

        Args:
            config_class: Config class to look for.

        Returns:
            type | None: The associated class, or ``None`` if no registry contains it.
        """
        registry_base: RegistryBase[Any]
        for registry_base in self.registry_bases:
            entry: Entry[Any] | None = registry_base.get_entry_from_config_class(
                config_class=config_class,
            )
            is_entry_found: bool = entry is not None
            if is_entry_found:
                return cast(Entry[Any], entry).class_
        return None

    def get_config_class_by_class(
        self,
        class_: type,
    ) -> type[BaseModel] | None:
        """Get the config class associated with a class, searching every registry.

        Args:
            class_: Class to look for.

        Returns:
            type[BaseModel] | None: The associated config class, or ``None`` if no
                registry contains it.
        """
        registry_base: RegistryBase[Any]
        for registry_base in self.registry_bases:
            entry: Entry[Any] | None = registry_base.get_entry_of_type(
                class_=class_,
            )
            is_entry_found: bool = entry is not None
            if is_entry_found:
                return cast(Entry[Any], entry).config_class
        return None

    def instantiate_from_dict(
        self,
        base_class: type[BaseT],
        config_dict: dict[str, Any],
    ) -> BaseT:
        """Build an object of a registered class from a raw configuration dictionary.

        The discriminator value in ``config_dict`` selects the config class among
        those registered for ``base_class``. The dictionary is validated into that
        config class, and the config object is passed to the associated class.

        Args:
            base_class: Base class whose registry holds the target class.
            config_dict: Raw configuration, including the discriminator field.

        Returns:
            BaseT: Instance of the registered class, built as ``class_(config)``.

        Raises:
            KeyError: If no registry exists for ``base_class``.
            ValueError: If the registry of ``base_class`` has no entries.
            pydantic.ValidationError: If ``config_dict`` matches no registered config class.
        """
        registry_base: RegistryBase[BaseT] = self._get_registry_base(
            base_class=base_class,
        )
        config: BaseModel = registry_base.config_type_adapter.validate_python(config_dict)
        entry: Entry[BaseT] = cast(
            Entry[BaseT],
            registry_base.get_entry_from_config_class(
                config_class=type(config),
            ),
        )
        class_constructor: Callable[[BaseModel], BaseT] = cast(
            Callable[[BaseModel], BaseT],
            entry.class_,
        )
        return class_constructor(config)
