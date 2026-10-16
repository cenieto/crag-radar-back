"""Generic registry that links classes to the class of their configuration object."""

from collections.abc import Mapping
from typing import Any, Callable, ClassVar, Generic, TypeVar, Union, cast, overload

from pydantic import TypeAdapter

T = TypeVar("T")
C = TypeVar("C")
R = TypeVar("R")
R_co = TypeVar("R_co", covariant=True)


class Config(Generic[R_co]):
    """Optional marker base class for configuration objects.

    Subclassing ``Config[X]`` declares that the configuration builds objects
    of type ``X``. This lets static type checkers infer the exact return type
    of :meth:`RegistryClass.generate`::

        class LinearConfig(Config[LinearModel]):
            ...

        ModelRegistry.generate(LinearConfig())  # inferred as LinearModel

    It has no runtime behaviour and is not required: configuration objects
    that do not inherit from it still work, and ``generate`` is then typed as
    the registry base type.
    """


class RegistryClass(Generic[T]):
    """Generic class registry keyed by configuration class.

    Each registered class is stored together with the class of its
    configuration object. Later, a configuration *instance* is enough to
    build an object of the registered class.

    The registry is generic over ``T``, the (base) type of the objects it
    produces, so it is not tied to any concrete class and can be reused.
    To get an independent registry, subclass it::

        class ModelRegistry(RegistryClass[BaseModel]):
            pass

        ModelRegistry.set(LinearModel, LinearConfig)
        model = ModelRegistry.generate(LinearConfig(alpha=0.1))

    Every subclass owns its own storage, so different registries never
    share entries. ``RegistryClass`` itself cannot be used directly.

    Registered classes must accept the configuration object as their single
    constructor argument: ``registered_class(config)``.

    Besides the class storage, every registry keeps a pydantic
    :class:`~pydantic.TypeAdapter` over the union of all registered
    configuration classes, which is used by :meth:`get_config_from_dict`
    to build a configuration object from a plain dictionary. Therefore,
    configuration classes must be types pydantic can validate (``BaseModel``,
    dataclasses, ``TypedDict``...).
    """

    _registry: ClassVar[dict[type, type]]
    _config_adapter: ClassVar["TypeAdapter[Any] | None"]

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        cls._registry = {}
        cls._config_adapter = None

    @classmethod
    def _storage(cls) -> dict[type, type]:
        """Return the storage of this registry.

        Raises:
            TypeError: If called on ``RegistryClass`` itself instead of a subclass.
        """
        if "_registry" not in cls.__dict__:
            raise TypeError(
                f"{cls.__name__} cannot be used directly; "
                "create a subclass, e.g. 'class MyRegistry(RegistryClass[Base])'."
            )
        return cls._registry

    @classmethod
    def _rebuild_config_adapter(cls) -> None:
        """Rebuild the ``TypeAdapter`` over the union of all registered config classes.

        Raises:
            pydantic.errors.PydanticSchemaGenerationError: If a registered
                configuration class cannot be handled by pydantic.
        """
        config_classes = tuple(cls._storage())
        # ``Union[(A, B)]`` is ``A | B``; with a single member it is just ``A``.
        cls._config_adapter = TypeAdapter(Union[config_classes])  # type: ignore[valid-type]

    @classmethod
    def set(cls, class_: Callable[[C], T], class_config: type[C]) -> None:
        """Register a class together with the class of its configuration object.

        Static type checkers verify that ``class_`` can be called with an
        instance of ``class_config`` and that it produces ``T``. The
        configuration class is also added to the ``TypeAdapter`` used by
        :meth:`get_config_from_dict`.

        Args:
            class_: Class to store. It must be instantiable as ``class_(config)``.
            class_config: Class of the configuration object associated with ``class_``.
                It must be a type that pydantic can validate.

        Returns:
            None.

        Raises:
            TypeError: If ``class_`` or ``class_config`` is not a class, or if
                called on ``RegistryClass`` itself.
            ValueError: If ``class_config`` is already registered.
            pydantic.errors.PydanticSchemaGenerationError: If ``class_config``
                cannot be handled by pydantic. The registry is left unchanged.
        """
        storage = cls._storage()
        if not isinstance(class_, type):
            raise TypeError(f"'class_' must be a class, got {class_!r}.")
        if not isinstance(class_config, type):
            raise TypeError(f"'class_config' must be a class, got {class_config!r}.")
        if class_config in storage:
            raise ValueError(
                f"Config class '{class_config.__name__}' is already registered "
                f"with '{storage[class_config].__name__}'."
            )
        storage[class_config] = class_
        try:
            cls._rebuild_config_adapter()
        except Exception:
            # Keep storage and adapter consistent if pydantic rejects the class.
            del storage[class_config]
            if storage:
                cls._rebuild_config_adapter()
            else:
                cls._config_adapter = None
            raise

    @classmethod
    def get(cls, class_config: type) -> type[T]:
        """Return the class registered for a configuration class.

        Args:
            class_config: Class of the configuration object.

        Returns:
            The class associated with ``class_config``.

        Raises:
            KeyError: If ``class_config`` has not been registered.
            TypeError: If called on ``RegistryClass`` itself.
        """
        storage = cls._storage()
        try:
            return storage[class_config]
        except KeyError:
            name = getattr(class_config, "__name__", repr(class_config))
            raise KeyError(f"No class registered for config class '{name}'.") from None

    @classmethod
    def get_config_from_dict(cls, config_dict: Mapping[str, Any]) -> Any:
        """Build a configuration object from a configuration dictionary.

        The dictionary is validated against the union of all registered
        configuration classes. If several classes could accept it, pydantic's
        *smart* union mode picks the best match. To make the choice
        unambiguous, give the configuration classes a discriminating field
        (e.g. ``type: Literal["date"]``) or forbid extra fields.

        Args:
            config_dict: Dictionary with the configuration values.

        Returns:
            An instance of the registered configuration class that matches
            ``config_dict``. It can be passed directly to :meth:`generate`.

        Raises:
            TypeError: If ``config_dict`` is not a mapping, or if called on
                ``RegistryClass`` itself.
            LookupError: If no configuration class is registered yet.
            pydantic.ValidationError: If ``config_dict`` does not match any
                registered configuration class. Its message lists why each
                candidate was rejected.
        """
        cls._storage()
        if not isinstance(config_dict, Mapping):
            raise TypeError(f"'config_dict' must be a mapping, got {type(config_dict).__name__}.")
        adapter = cls._config_adapter
        if adapter is None:
            raise LookupError(f"No config classes are registered in '{cls.__name__}'.")
        return adapter.validate_python(config_dict)

    @overload
    @classmethod
    def generate(cls, object_config: Config[R]) -> R: ...

    @overload
    @classmethod
    def generate(cls, object_config: Any) -> T: ...

    @classmethod
    def generate(cls, object_config: Any) -> Any:
        """Instantiate the registered class using a configuration object.

        The class is looked up by the exact type of ``object_config`` and
        instantiated as ``registered_class(object_config)``.

        Typing: if ``object_config`` is an instance of ``Config[X]`` the
        result is typed as ``X``; otherwise it is typed as ``T``.

        Args:
            object_config: Configuration instance whose class was registered with ``set``.

        Returns:
            A new instance of the class registered for ``type(object_config)``.

        Raises:
            KeyError: If ``type(object_config)`` has not been registered.
            TypeError: If called on ``RegistryClass`` itself.
        """
        factory = cast("Callable[[Any], T]", cls.get(type(object_config)))
        return factory(object_config)
