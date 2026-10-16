from __future__ import annotations

from pathlib import Path

import pytest
from test.config import FIXTURES_DIR, TMP_DIR

from repos.abcs import NamedFile
from repos.path.fixed import FixedPathGenerator, FixedPathGeneratorConfig


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
def fixed_path_generator_config(
    base_path: str,
) -> FixedPathGeneratorConfig:
    return FixedPathGeneratorConfig(
        base_path=base_path,
    )


@pytest.fixture
def fixed_path_generator(
    fixed_path_generator_config: FixedPathGeneratorConfig,
) -> FixedPathGenerator:
    return FixedPathGenerator(
        config=fixed_path_generator_config,
    )


def test_fixed_path_generator(
    base_path: Path,
    fixed_path_generator: FixedPathGenerator,
    dummy_file: DummyFile,
):
    generated_path = fixed_path_generator.generate_path(dummy_file)

    assert str(generated_path) == f"{base_path}/{dummy_file.name}"


def test_fixed_path_generator_fixture_file_text(
    base_path: Path,
    fixed_path_generator: FixedPathGenerator,
    test_file_text: NamedFile,
):
    generated_path = fixed_path_generator.generate_path(test_file_text)
    assert str(generated_path) == f"{base_path}/{Path(test_file_text.name).name}"


def test_fixed_path_generator_fixture_file_binary(
    fixed_path_generator: FixedPathGenerator,
    base_path: Path,
    test_file_binary: NamedFile,
):
    generated_path = fixed_path_generator.generate_path(test_file_binary)

    assert str(generated_path) == f"{base_path}/{Path(test_file_binary.name).name}"
