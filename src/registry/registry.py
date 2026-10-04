"""Generic registry that links classes to the class of their configuration object."""

from typing import Any, Callable, ClassVar, Generic, TypeVar, overload, cast

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
    """

    _registry: ClassVar[dict[type, type]]

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        cls._registry = {}

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
    def set(cls, class_: Callable[[C], T], class_config: type[C]) -> None:
        """Register a class together with the class of its configuration object.

        Static type checkers verify that ``class_`` can be called with an
        instance of ``class_config`` and that it produces ``T``.

        Args:
            class_: Class to store. It must be instantiable as ``class_(config)``.
            class_config: Class of the configuration object associated with ``class_``.

        Returns:
            None.

        Raises:
            TypeError: If ``class_`` or ``class_config`` is not a class, or if
                called on ``RegistryClass`` itself.
            ValueError: If ``class_config`` is already registered.
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