from __future__ import annotations

import shutil
from typing import BinaryIO, TextIO

import pytest

from store_files.local import LocalStore
from store_files.path_generator import DefaultPathGenerator
from test.config import FIXTURES_DIR, TMP_DIR


@pytest.fixture
def base_path() -> str:
    yield TMP_DIR / "test_dir"
    
    shutil.rmtree(TMP_DIR , ignore_errors=True)


@pytest.fixture
def test_file_name() -> str:
    return FIXTURES_DIR / "store_files" / "example.md"


@pytest.fixture
def test_file_text(
    test_file_name: str,
) -> TextIO | BinaryIO:
    with open(test_file_name, "r") as f:
        yield f


@pytest.fixture
def test_file_binary(
    test_file_name: str,
) -> TextIO | BinaryIO:
    with open(test_file_name, "rb") as f:
        yield f
        
        
def test_local_store_with_default_path_generator_file_object_text(
    base_path: str,
    test_file_name: str,
    test_file_text: TextIO,
):
    path_generator = DefaultPathGenerator(base_path=base_path)
    store = LocalStore(path_generator=path_generator)

    out_path = store.save(test_file_text)
        
    assert out_path    
    assert out_path.exists()
        
    with open(test_file_name, "r") as f:
        assert out_path.read_text() == f.read()
        
        
def test_local_store_with_default_path_generator_file_object_binary(
    base_path: str,
    test_file_name: str,
    test_file_binary: BinaryIO,
):
    path_generator = DefaultPathGenerator(base_path=base_path)
    store = LocalStore(path_generator=path_generator)

    out_path = store.save(test_file_binary)
        
    assert out_path    
    assert out_path.exists()
        
    with open(test_file_name, "r") as f:
        assert out_path.read_text() == f.read()
