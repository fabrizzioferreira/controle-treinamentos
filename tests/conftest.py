from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import pytest

# Garante que a raiz do projeto esteja no sys.path durante a coleta do pytest.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
project_root_str = str(PROJECT_ROOT)
if project_root_str not in sys.path:
    sys.path.insert(0, project_root_str)


@pytest.fixture
def media_storage_tmp_path():
    with tempfile.TemporaryDirectory(prefix="controle-media-storage-") as raw_path:
        yield Path(raw_path).resolve()


@pytest.fixture
def safe_filesystem_tmp_path():
    with tempfile.TemporaryDirectory(prefix="controle-test-fs-") as raw_path:
        yield Path(raw_path).resolve()
