from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from casm_world.paths import (
    APPROVED_RAW_ROOT,
    REQUIRED_FORBIDDEN_ROOTS,
    SourceContractError,
    SourceRecord,
    assert_allowed_source_path,
    load_source_catalog,
    verify_all_sources,
    verify_source,
)


EXPECTED_SOURCE_COUNT = 27


def test_catalog_uses_only_verified_approved_snapshots():
    catalog = load_source_catalog()
    assert catalog.raw_root == APPROVED_RAW_ROOT.resolve()
    assert len(catalog.sources) == EXPECTED_SOURCE_COUNT
    assert len({row.source_id for row in catalog.sources.values()}) == len(
        catalog.sources
    )
    assert len({row.path for row in catalog.sources.values()}) == len(catalog.sources)
    for row in catalog.sources.values():
        assert row.path.is_file()
        assert row.path.is_relative_to(catalog.raw_root)
        assert len(row.expected_sha256) == 64


def test_all_configured_snapshots_match_manifest_sha256():
    catalog = load_source_catalog()
    digests = verify_all_sources(catalog)
    assert set(digests) == set(catalog.sources)
    assert all(digests[key] == row.expected_sha256 for key, row in catalog.sources.items())


@pytest.mark.parametrize(
    "forbidden_path",
    [
        "/root/data/CASM/SILK Model/baseline/input.xlsx",
        "/root/data/CASM/casm_world/output/results.csv",
        "/root/data/CASM/casm_py/casm_world/cw/data.py",
        "/root/data/CASM/casm_world_2050/data/raw/fao/bilateral/trade.csv",
    ],
)
def test_legacy_silk_and_bilateral_paths_are_explicitly_forbidden(forbidden_path):
    with pytest.raises(SourceContractError, match="Forbidden"):
        assert_allowed_source_path(forbidden_path, require_exists=False)


def test_relative_escape_from_raw_root_is_rejected():
    escaped = APPROVED_RAW_ROOT / ".." / "metadata" / "source_manifest.csv"
    with pytest.raises(SourceContractError, match="approved raw root"):
        assert_allowed_source_path(escaped)


def test_sha_mismatch_is_fatal(tmp_path: Path):
    source = tmp_path / "snapshot.bin"
    source.write_bytes(b"immutable snapshot")
    wrong = "0" * 64
    record = SourceRecord(
        key="example",
        source_id="EXAMPLE",
        provider="FAOSTAT",
        path=source,
        expected_sha256=wrong,
    )
    assert hashlib.sha256(source.read_bytes()).hexdigest() != wrong
    with pytest.raises(SourceContractError, match="SHA-256 mismatch"):
        verify_source(record)


def test_required_legacy_roots_are_not_the_approved_snapshot_root():
    approved = APPROVED_RAW_ROOT.resolve()
    assert all(root.resolve() != approved for root in REQUIRED_FORBIDDEN_ROOTS)
