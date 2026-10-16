from __future__ import annotations

from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from test.config import FIXTURES_DIR, TMP_DIR

from repos.abcs import NamedFile
from repos.path.date import DatePathGenerator, DatePathGeneratorConfig


class DummyFile:
    def __init__(self, name):
        self.name = name


@pytest.fixture
def base_path() -> Path:
    base_path: Path = Path("/test_path")
    return base_path


@pytest.fixture
def dummy_file_name() -> str:
    return "test_file.txt"


@pytest.fixture
def dummy_file(
    dummy_file_name: str,
) -> DummyFile:
    return DummyFile(name=dummy_file_name)


@pytest.fixture
def test_file_name() -> Path:
    return FIXTURES_DIR / "storers" / "example.md"


@pytest.fixture
def test_file_text(
    test_file_name: Path,
) -> NamedFile:
    with open(test_file_name) as f:
        yield f


@pytest.fixture
def test_file_binary(
    test_file_name: Path,
) -> NamedFile:
    with open(test_file_name, "rb") as f:
        yield f


@pytest.fixture
def date_path_generator_config(
    base_path: str,
) -> DatePathGeneratorConfig:
    return DatePathGeneratorConfig(
        base_path=base_path,
    )


@pytest.fixture
def date_path_generator(
    date_path_generator_config: DatePathGeneratorConfig,
) -> DatePathGenerator:
    return DatePathGenerator(
        config=date_path_generator_config,
    )


def test_date_path_generator_config_timezone_validation():
    # Valid timezone
    config = DatePathGeneratorConfig(base_path=Path("/test"), timezone="Europe/Madrid")
    assert config.timezone == "Europe/Madrid"

    # Invalid timezone
    with pytest.raises(ValueError):
        DatePathGeneratorConfig(base_path=Path("/test"), timezone="Invalid/Timezone")


def test_date_path_generator(
    base_path: Path,
    date_path_generator: DatePathGenerator,
    dummy_file: DummyFile,
):
    generated_path = date_path_generator.generate_path(dummy_file)

    timezone: str = ZoneInfo("UTC")
    date_today = datetime.now(tz=timezone).date()
    date_subdir = date_today.strftime("%Y/%m/%d")

    assert str(generated_path) == str(base_path / date_subdir / dummy_file.name)

    timezone: str = ZoneInfo("Europe/Madrid")
    date_today = datetime.now(tz=timezone).date()
    date_subdir = date_today.strftime("%Y/%m/%d")

    assert str(generated_path) == str(base_path / date_subdir / dummy_file.name)


def test_date_path_generator_fixture_file_text(
    base_path: Path,
    date_path_generator: DatePathGenerator,
    test_file_text: NamedFile,
):
    generated_path = date_path_generator.generate_path(test_file_text)

    timezone: str = ZoneInfo("Europe/Madrid")
    date_today = datetime.now(tz=timezone).date()
    date_subdir = date_today.strftime("%Y/%m/%d")

    assert str(generated_path) == str(base_path / date_subdir / Path(test_file_text.name).name)


def test_date_path_generator_fixture_file_binary(
    date_path_generator: DatePathGenerator,
    base_path: Path,
    test_file_binary: NamedFile,
):
    generated_path = date_path_generator.generate_path(test_file_binary)

    timezone: str = ZoneInfo("Europe/Madrid")
    date_today = datetime.now(tz=timezone).date()
    date_subdir = date_today.strftime("%Y/%m/%d")

    assert str(generated_path) == str(base_path / date_subdir / Path(test_file_binary.name).name)
