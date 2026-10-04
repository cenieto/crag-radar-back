from __future__ import annotations

import datetime
import shutil
from pathlib import Path
from typing import BinaryIO, TextIO

import pytest
from test.config import FIXTURES_DIR

from tmp.path_generator import DatePathGenerator, DefaultPathGenerator


class DummyFile:
    def __init__(self, name):
        self.name = name
        
        
@pytest.fixture
def base_path() -> str:
    yield "/tmp/test_dir"
    
    shutil.rmtree("/tmp/test_dir", ignore_errors=True)


@pytest.fixture
def dummy_file_name() -> str:
    return "test_file.txt"


@pytest.fixture
def dummy_file(
    dummy_file_name: str,
) -> DummyFile:
    return DummyFile(name=dummy_file_name)


@pytest.fixture
def test_file_name() -> str:
    return FIXTURES_DIR / "storers" / "example.md"


@pytest.fixture
def test_file_text(
    test_file_name: str,
) -> TextIO | BinaryIO:
    with open(test_file_name) as f:
        yield f


@pytest.fixture
def test_file_binary(
    test_file_name: str,
) -> TextIO | BinaryIO:
    with open(test_file_name, "rb") as f:
        yield f


def test_default_path_generator(
    base_path: str,
    dummy_file: DummyFile,
):
    path_generator = DefaultPathGenerator(base_path=base_path)
    
    generated_path = path_generator.generate_path(dummy_file)

    assert str(generated_path) == f"{base_path}/{dummy_file.name}"


def test_default_path_generator_fixture_file_text(
    base_path: str,
    test_file_text: TextIO,
):
    path_generator = DefaultPathGenerator(base_path=base_path)
    
    generated_path = path_generator.generate_path(test_file_text)
        
    assert str(generated_path) == f"{base_path}/{Path(test_file_text.name).name}"
    

def test_default_path_generator_fixture_file_binary(
    base_path: str,
    test_file_binary: BinaryIO,
):
    path_generator = DefaultPathGenerator(base_path=base_path)
    
    generated_path = path_generator.generate_path(test_file_binary)
        
    assert str(generated_path) == f"{base_path}/{Path(test_file_binary.name).name}"


def test_date_path_generator(
    base_path: str,
    dummy_file: DummyFile,
):
    path_generator = DatePathGenerator(base_path=base_path)
    
    date: datetime.date = datetime.date.today()
            
    date_subdir = date.strftime("%Y/%m/%d")
    
    generated_path = path_generator.generate_path(dummy_file)

    assert str(generated_path) == f"{base_path}/{date_subdir}/{dummy_file.name}"
    

def test_date_path_generator_fixture_file_text(
    base_path: str,
    test_file_text: TextIO,
):
    path_generator = DatePathGenerator(base_path=base_path)
    
    date: datetime.date = datetime.date.today()
            
    date_subdir = date.strftime("%Y/%m/%d")
    
    generated_path = path_generator.generate_path(test_file_text)

    assert str(generated_path) == f"{base_path}/{date_subdir}/{Path(test_file_text.name).name}"
    
    

def test_date_path_generator_fixture_file_binary(
    base_path: str,
    test_file_binary: BinaryIO,
):
    path_generator = DatePathGenerator(base_path=base_path)
    
    date: datetime.date = datetime.date.today()
            
    date_subdir = date.strftime("%Y/%m/%d")
    
    generated_path = path_generator.generate_path(test_file_binary)

    assert str(generated_path) == f"{base_path}/{date_subdir}/{Path(test_file_binary.name).name}"
    
