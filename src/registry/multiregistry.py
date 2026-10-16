"""Singleton that manages one :class:`RegistryClass` per base type."""

import threading
import types
from collections.abc import Mapping
from typing import Any, ClassVar, TypeVar, cast, Callable

from registry.registry import RegistryClass

T = TypeVar("T")
C = TypeVar("C")
U = TypeVar("U")


class _SingletonMeta(type):
    """Metaclass that turns every class using it into a thread-safe singleton.

    Each class (including subclasses) gets its own single instance.
    """

    _instances: ClassVar[dict[type, Any]] = {}
    _lock: ClassVar[threading.RLock] = threading.RLock()

    def __call__(cls, *args: Any, **kwargs: Any) -> Any:
        instances = _SingletonMeta._instances
        if cls not in instances:
            with _SingletonMeta._lock:
                if cls not in instances:
                    instances[cls] = super().__call__(*args, **kwargs)
        return instances[cls]

    def reset_instance(cls) -> None:
        """Discard the singleton instance of this class. Intended for tests."""
        with _SingletonMeta._lock:
            _SingletonMeta._instances.pop(cls, None)


class MultiRegistryClass(metaclass=_SingletonMeta):
    """Singleton holding one registry per base type.

    ``MultiRegistryClass()`` always returns the same instance. Every registry
    is an independent subclass of :class:`RegistryClass`, so registries never
    share entries::

        multi = MultiRegistryClass()
        multi.create_registry(PathGenerator, nested={"storer": Storer})
        multi.create_registry(Storer)
        multi.get_registry(Storer).set(DiskStorer, DiskStorerConfig)
        multi.get_registry(PathGenerator).set(DatePathGenerator, DatePathConfig)

        generator = multi.instantiate_from_dict(
            PathGenerator,
            {"base_path": "/data", "storer": {"root": "/mnt"}},
        )
    """

    def __init__(self) -> None:
        self._registries: dict[type, type[RegistryClass[Any]]] = {}
        self._nested_fields: dict[type, dict[str, type]] = {}

    def create_registry(
        self,
        base_type: type[T],
        nested: Mapping[str, type] | None = None,
    ) -> type[RegistryClass[T]]:
        """Create a new registry for a specific base type.

        Args:
            base_type: Base type of the objects produced by the new registry.
            nested: Optional mapping ``{config_field_name: nested_base_type}``.
                In :meth:`instantiate_from_dict`, when a field in this mapping
                holds a dictionary, it is replaced by an object built from the
                registry of ``nested_base_type``. The nested registry does not
                need to exist yet at this point.

        Returns:
            The newly created registry (a subclass of ``RegistryClass``).

        Raises:
            ValueError: If a registry already exists for ``base_type``.
        """
        if base_type in self._registries:
            raise ValueError(f"A registry for base type '{base_type.__name__}' already exists.")
        registry = cast(
            "type[RegistryClass[T]]",
            types.new_class(
                f"{base_type.__name__}Registry",
                (RegistryClass[base_type],),  # type: ignore[valid-type]
            ),
        )
        self._registries[base_type] = registry
        self._nested_fields[base_type] = dict(nested or {})
        return registry

    def get_registry(self, base_type: type[T]) -> type[RegistryClass[T]]:
        """Get the registry for a specific base type.

        Args:
            base_type: Base type whose registry is requested.

        Returns:
            The registry associated with ``base_type``.

        Raises:
            KeyError: If no registry exists for ``base_type``.
        """
        try:
            return cast("type[RegistryClass[T]]", self._registries[base_type])
        except KeyError:
            name = getattr(base_type, "__name__", repr(base_type))
            raise KeyError(f"No registry found for base type '{name}'.") from None

    def get_registered_class(self, base_type: type[T], class_config: type) -> type[T]:
        """Get the class registered for a base type and a configuration class.

        Args:
            base_type: Base type whose registry is used.
            class_config: Configuration class the wanted class was registered with.

        Returns:
            The class associated with ``class_config`` in that registry.

        Raises:
            KeyError: If there is no registry for ``base_type`` or no class
                registered for ``class_config``.
        """
        return self.get_registry(base_type).get(class_config)

    def instantiate(self, base_type: type[T], object_config: Any) -> T:
        """Instantiate the class registered for a configuration object.

        Args:
            base_type: Base type whose registry is used.
            object_config: Configuration instance whose class was registered.

        Returns:
            A new instance built from ``object_config``.

        Raises:
            KeyError: If there is no registry for ``base_type`` or the type of
                ``object_config`` is not registered.
        """
        return self.get_registry(base_type).generate(object_config)

    def instantiate_from_dict(self, base_type: type[T], config_dict: Mapping[str, Any]) -> T:
        """Instantiate a registered class from a configuration dictionary.

        Fields declared in ``nested`` when the registry was created are first
        replaced, recursively, by objects built from their own registries.
        Values that are not dictionaries (e.g. already built objects) are left
        untouched. ``config_dict`` itself is not modified.

        Args:
            base_type: Base type whose registry is used.
            config_dict: Configuration values for the object.

        Returns:
            A new instance of the class matching ``config_dict``.

        Raises:
            KeyError: If there is no registry for ``base_type`` (or for a
                nested base type).
            LookupError: If the registry has no configuration classes.
            pydantic.ValidationError: If no configuration class matches the
                resolved dictionary.
        """
        registry = self.get_registry(base_type)
        resolved = dict(config_dict)
        for field, nested_base_type in self._nested_fields[base_type].items():
            value = resolved.get(field)
            if isinstance(value, Mapping):
                resolved[field] = self.instantiate_from_dict(nested_base_type, value)
        config = registry.get_config_from_dict(resolved)
        return registry.generate(config)

    def register(
        self,
        base_type: type[T],
        class_: Callable[[C], T],
        class_config: type[C],
    ) -> None:
        """Register a class in the registry of a base type.

        Shortcut for ``get_registry(base_type).set(class_, class_config)``
        that also checks that ``class_`` really derives from ``base_type``.

        Args:
            base_type: Base type whose registry is used.
            class_: Class to register. It must be instantiable as ``class_(config)``.
            class_config: Class of the configuration object associated with ``class_``.

        Raises:
            KeyError: If there is no registry for ``base_type``.
            TypeError: If ``class_`` is not a subclass of ``base_type``, or if
                ``class_`` or ``class_config`` is not a class.
            ValueError: If ``class_config`` is already registered in that registry.
        """
        if isinstance(class_, type) and not issubclass(class_, base_type):
            raise TypeError(f"'{class_.__name__}' is not a subclass of '{base_type.__name__}'.")
        self.get_registry(base_type).set(class_, class_config)

    def register_as(
        self,
        base_type: type[T],
        class_config: type[Any],
    ) -> Callable[[type[U]], type[U]]:
        """Return a class decorator that registers the decorated class.

        The decorated class is returned unchanged, so it can be used normally
        afterwards::

            @MultiRegistryClass().register_as(PathGenerator, DatePathGeneratorConfig)
            class DatePathGenerator(PathGenerator):
                def __init__(self, config: DatePathGeneratorConfig) -> None: ...

        Args:
            base_type: Base type whose registry is used.
            class_config: Class of the configuration object associated with
                the decorated class.

        Returns:
            A decorator that registers a class and returns it.

        Raises:
            KeyError, TypeError, ValueError: Same as :meth:`register`, raised
                when the decorator is applied.
        """

        def decorator(class_: type[U]) -> type[U]:
            self.register(base_type, cast("Callable[[Any], T]", class_), class_config)
            return class_

        return decorator


def register_class(base_type: type[Any], class_config: type[Any]) -> Callable[[type[U]], type[U]]:
    """Class decorator that registers a class in the global ``MultiRegistryClass``."""
    print(base_type, class_config)
    return MultiRegistryClass().register_as(base_type, class_config)
