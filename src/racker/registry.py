from pydantic import BaseModel, model_validator


class Entry(BaseModel):
    _discriminator: str = "type"

    base_class: type
    class_: type
    config_class: type[BaseModel]

    @model_validator(mode="after")
    def validate_entry(self) -> "Entry":
        if not issubclass(self.class_, self.base_class):
            raise ValueError(f"{self.class_} is not a subclass of {self.base_class}")

        if self._discriminator not in getattr(self.config_class, "model_fields", {}):
            raise ValueError(
                f"{self.config_class} has no discriminator field: 'default={self._discriminator!r}'"
            )

        return self


class RegistryBase:
    def __init__(
        self,
        base_class: type,
    ):
        self._base_class: type = base_class
        self._entries: dict[type[BaseModel], Entry] = {}

    @property
    def config_classes(
        self,
    ) -> type[BaseModel]:
        return list(self._entries.keys())

    @property
    def classes_(
        self,
    ) -> type:
        return [entry.class_ for entry in self._entries.values()]

    def is_entry_registered(
        self,
        entry: Entry,
    ) -> bool:
        return entry in self._entries.values()

    def is_entry_of_base_type(
        self,
        entry: Entry,
    ) -> bool:
        return entry.base_class == self._base_class

    def _check_entry_for_register(
        self,
        entry: Entry,
    ) -> None:
        # TODO add test
        if self.is_entry_registered(
            entry=entry,
        ):
            raise ValueError(f"Entry for {entry.class_} already registered")

        if not self.is_entry_of_base_type(
            entry=entry,
        ):
            raise ValueError(f"Entry for {entry.class_} is not of base class: {self._base_class}")

    def register(
        self,
        entry: Entry,
    ):
        self._check_entry_for_register(
            entry=entry,
        )
        self._entries[entry.config_class] = entry

    def get_entry_from_config_class(
        self,
        config_class: type[BaseModel],
    ) -> Entry:
        return self._entries[config_class]

    def get_entry_from_class_(
        self,
        class_: type,
    ) -> Entry | None:
        for _, entry in self._entries.items():
            if class_ == entry.class_:
                return entry
        return None
