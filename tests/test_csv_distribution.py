"""Checks that the committed CSV-distribution ZIP matches the canonical tables and rebuilds identically."""

import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from build_csv_distribution import DEFAULT_OUTPUT, DEFAULT_SOURCE, TABLES, build  # noqa: E402


def test_zip_contains_the_canonical_tables_byte_for_byte():
    with zipfile.ZipFile(DEFAULT_OUTPUT) as zf:
        assert sorted(zf.namelist()) == [f"{DEFAULT_SOURCE.name}/{t}" for t in TABLES]
        for name in TABLES:
            assert zf.read(f"{DEFAULT_SOURCE.name}/{name}") == (DEFAULT_SOURCE / name).read_bytes()


def test_committed_zip_is_reproducible(tmp_path):
    rebuilt = tmp_path / "rebuilt.zip"
    build(DEFAULT_SOURCE, rebuilt)
    assert rebuilt.read_bytes() == DEFAULT_OUTPUT.read_bytes()
