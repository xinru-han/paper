"""Strict data-source paths for the clean CASM-World rebuild.

The rebuild deliberately has no runtime dependency on earlier CASM-World,
SILK, or bilateral-trade files.  Every data file must be named in the YAML
catalog, live below the one approved snapshot root, have a ``verified`` row
in the upstream source manifest, and match that row's SHA-256 digest.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "data_sources.yaml"
APPROVED_RAW_ROOT = Path("/root/data/CASM/casm_world_2050/data/raw")
APPROVED_MANIFEST_PATH = Path(
    "/root/data/CASM/casm_world_2050/data/metadata/source_manifest.csv"
)
REQUIRED_FORBIDDEN_FRAGMENTS = frozenset({"silk model", "bilateral"})
REQUIRED_FORBIDDEN_ROOTS = (
    Path("/root/data/CASM/casm_world"),
    Path("/root/data/CASM/casm_py/casm_world"),
)
REQUIRED_MANIFEST_COLUMNS = frozenset(
    {"source_id", "provider", "sha256", "status"}
)
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


class SourceContractError(ValueError):
    """Raised when a path or manifest entry violates the data contract."""


@dataclass(frozen=True)
class ManifestEntry:
    source_id: str
    provider: str
    sha256: str
    status: str


@dataclass(frozen=True)
class SourceRecord:
    key: str
    source_id: str
    provider: str
    path: Path
    expected_sha256: str


@dataclass(frozen=True)
class SourceCatalog:
    raw_root: Path
    manifest_path: Path
    sources: Mapping[str, SourceRecord]
    forbidden_fragments: tuple[str, ...]
    forbidden_roots: tuple[Path, ...]

    def source(self, key: str) -> SourceRecord:
        """Return a configured source, failing on an unknown logical key."""

        try:
            return self.sources[key]
        except KeyError as exc:
            raise SourceContractError(f"Unknown data source key: {key!r}") from exc


def _resolved(path: Path, *, strict: bool) -> Path:
    try:
        return path.expanduser().resolve(strict=strict)
    except FileNotFoundError as exc:
        raise SourceContractError(f"Required source path does not exist: {path}") from exc


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def assert_allowed_source_path(
    path: Path | str,
    *,
    trusted_root: Path = APPROVED_RAW_ROOT,
    forbidden_fragments: Iterable[str] = REQUIRED_FORBIDDEN_FRAGMENTS,
    forbidden_roots: Iterable[Path] = REQUIRED_FORBIDDEN_ROOTS,
    require_exists: bool = True,
) -> Path:
    """Resolve and validate a prospective input path.

    Resolution occurs before containment testing, so ``..`` and symlink
    escapes cannot bypass the approved-root rule.  Forbidden dependencies are
    checked first to make failures explicit rather than reporting them merely
    as generic out-of-root paths.
    """

    candidate = _resolved(Path(path), strict=require_exists)
    root = _resolved(Path(trusted_root), strict=True)
    folded = candidate.as_posix().casefold()

    for fragment in forbidden_fragments:
        token = str(fragment).strip().casefold()
        if token and token in folded:
            raise SourceContractError(
                f"Forbidden data dependency fragment {fragment!r}: {candidate}"
            )

    for forbidden_root in forbidden_roots:
        blocked = _resolved(Path(forbidden_root), strict=False)
        if _is_within(candidate, blocked):
            raise SourceContractError(
                f"Forbidden legacy-model data dependency: {candidate}"
            )

    if not _is_within(candidate, root) or candidate == root:
        raise SourceContractError(
            f"Source must be a file below the approved raw root {root}: {candidate}"
        )
    if require_exists and not candidate.is_file():
        raise SourceContractError(f"Configured source is not a regular file: {candidate}")
    return candidate


def load_verified_manifest(
    manifest_path: Path | str = APPROVED_MANIFEST_PATH,
) -> dict[str, ManifestEntry]:
    """Load unique, well-formed manifest entries.

    Rows of any status are retained so the catalog loader can issue a precise
    error when a configured source is not ``verified``.
    """

    path = _resolved(Path(manifest_path), strict=True)
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        columns = set(reader.fieldnames or ())
        missing = REQUIRED_MANIFEST_COLUMNS - columns
        if missing:
            raise SourceContractError(
                f"Source manifest is missing columns: {sorted(missing)}"
            )
        entries: dict[str, ManifestEntry] = {}
        for row_number, row in enumerate(reader, start=2):
            source_id = (row.get("source_id") or "").strip()
            provider = (row.get("provider") or "").strip()
            digest = (row.get("sha256") or "").strip().casefold()
            status = (row.get("status") or "").strip()
            if not source_id:
                raise SourceContractError(
                    f"Blank source_id in manifest row {row_number}"
                )
            if source_id in entries:
                raise SourceContractError(
                    f"Duplicate source_id in manifest: {source_id}"
                )
            if not provider:
                raise SourceContractError(
                    f"Blank provider for manifest source {source_id}"
                )
            if not SHA256_PATTERN.fullmatch(digest):
                raise SourceContractError(
                    f"Invalid SHA-256 for manifest source {source_id}"
                )
            entries[source_id] = ManifestEntry(
                source_id=source_id,
                provider=provider,
                sha256=digest,
                status=status,
            )
    return entries


def _require_mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise SourceContractError(f"{label} must be a mapping")
    return value


def load_source_catalog(
    config_path: Path | str = DEFAULT_CONFIG_PATH,
) -> SourceCatalog:
    """Load the YAML catalog and reconcile every source to the manifest."""

    config_file = _resolved(Path(config_path), strict=True)
    raw_config = yaml.safe_load(config_file.read_text(encoding="utf-8"))
    config = _require_mapping(raw_config, "data source configuration")
    if config.get("schema_version") != 1:
        raise SourceContractError("data_sources.yaml schema_version must equal 1")

    contract = _require_mapping(config.get("contract"), "contract")
    raw_root = _resolved(Path(str(contract.get("trusted_raw_root", ""))), strict=True)
    manifest_path = _resolved(
        Path(str(contract.get("source_manifest", ""))), strict=True
    )
    if raw_root != _resolved(APPROVED_RAW_ROOT, strict=True):
        raise SourceContractError(
            f"trusted_raw_root must be the approved snapshot root {APPROVED_RAW_ROOT}"
        )
    if manifest_path != _resolved(APPROVED_MANIFEST_PATH, strict=True):
        raise SourceContractError(
            f"source_manifest must be {APPROVED_MANIFEST_PATH}"
        )

    required_status = str(contract.get("required_manifest_status", "")).casefold()
    if required_status != "verified":
        raise SourceContractError("required_manifest_status must be 'verified'")

    allowed_providers_raw = contract.get("allowed_providers")
    if not isinstance(allowed_providers_raw, list) or not allowed_providers_raw:
        raise SourceContractError("allowed_providers must be a non-empty list")
    allowed_providers = {str(value).strip() for value in allowed_providers_raw}

    fragments_raw = contract.get("forbidden_path_fragments")
    if not isinstance(fragments_raw, list):
        raise SourceContractError("forbidden_path_fragments must be a list")
    forbidden_fragments = tuple(str(value).strip() for value in fragments_raw)
    fragment_set = {value.casefold() for value in forbidden_fragments}
    if not REQUIRED_FORBIDDEN_FRAGMENTS.issubset(fragment_set):
        raise SourceContractError(
            "forbidden_path_fragments must explicitly include SILK Model and bilateral"
        )

    roots_raw = contract.get("forbidden_roots")
    if not isinstance(roots_raw, list):
        raise SourceContractError("forbidden_roots must be a list")
    forbidden_roots = tuple(_resolved(Path(str(value)), strict=False) for value in roots_raw)
    configured_root_set = set(forbidden_roots)
    required_root_set = {
        _resolved(path, strict=False) for path in REQUIRED_FORBIDDEN_ROOTS
    }
    if not required_root_set.issubset(configured_root_set):
        raise SourceContractError(
            "forbidden_roots must explicitly include both legacy CASM-World trees"
        )

    manifest = load_verified_manifest(manifest_path)
    source_config = _require_mapping(config.get("sources"), "sources")
    if not source_config:
        raise SourceContractError("At least one data source must be configured")

    records: dict[str, SourceRecord] = {}
    seen_source_ids: set[str] = set()
    seen_paths: set[Path] = set()
    for key, raw_spec in source_config.items():
        logical_key = str(key).strip()
        if not logical_key:
            raise SourceContractError("Source keys must not be blank")
        spec = _require_mapping(raw_spec, f"source {logical_key!r}")
        source_id = str(spec.get("source_id", "")).strip()
        relative_text = str(spec.get("relative_path", "")).strip()
        relative_path = Path(relative_text)
        if not source_id or not relative_text:
            raise SourceContractError(
                f"Source {logical_key!r} needs source_id and relative_path"
            )
        if relative_path.is_absolute():
            raise SourceContractError(
                f"Source {logical_key!r} relative_path must not be absolute"
            )
        if source_id in seen_source_ids:
            raise SourceContractError(f"Duplicate configured source_id: {source_id}")
        entry = manifest.get(source_id)
        if entry is None:
            raise SourceContractError(
                f"Configured source_id is absent from the manifest: {source_id}"
            )
        if entry.status.casefold() != required_status:
            raise SourceContractError(
                f"Manifest source {source_id} is not verified: {entry.status!r}"
            )
        if entry.provider not in allowed_providers:
            raise SourceContractError(
                f"Provider is outside the approved set for {source_id}: {entry.provider}"
            )
        source_path = assert_allowed_source_path(
            raw_root / relative_path,
            trusted_root=raw_root,
            forbidden_fragments=forbidden_fragments,
            forbidden_roots=forbidden_roots,
        )
        if source_path in seen_paths:
            raise SourceContractError(f"Duplicate configured source path: {source_path}")
        records[logical_key] = SourceRecord(
            key=logical_key,
            source_id=source_id,
            provider=entry.provider,
            path=source_path,
            expected_sha256=entry.sha256,
        )
        seen_source_ids.add(source_id)
        seen_paths.add(source_path)

    return SourceCatalog(
        raw_root=raw_root,
        manifest_path=manifest_path,
        sources=records,
        forbidden_fragments=forbidden_fragments,
        forbidden_roots=forbidden_roots,
    )


def sha256_file(path: Path | str, *, chunk_size: int = 4 * 1024 * 1024) -> str:
    """Return the lowercase SHA-256 digest of a file without loading it whole."""

    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    source_path = _resolved(Path(path), strict=True)
    if not source_path.is_file():
        raise SourceContractError(f"Cannot hash a non-file source: {source_path}")
    digest = hashlib.sha256()
    with source_path.open("rb") as handle:
        for block in iter(lambda: handle.read(chunk_size), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_source(record: SourceRecord) -> str:
    """Verify one source against its manifest digest and return the digest."""

    actual = sha256_file(record.path)
    if actual != record.expected_sha256:
        raise SourceContractError(
            f"SHA-256 mismatch for {record.key} ({record.source_id}): "
            f"expected {record.expected_sha256}, got {actual}"
        )
    return actual


def verify_all_sources(
    catalog: SourceCatalog | None = None,
) -> dict[str, str]:
    """Verify every configured snapshot and return digests by logical key."""

    active_catalog = catalog or load_source_catalog()
    return {
        key: verify_source(active_catalog.sources[key])
        for key in sorted(active_catalog.sources)
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument(
        "--skip-sha256",
        action="store_true",
        help="validate paths and manifest rows without reading every source file",
    )
    args = parser.parse_args()
    catalog = load_source_catalog(args.config)
    if args.skip_sha256:
        print(f"validated {len(catalog.sources)} source contracts")
    else:
        verified = verify_all_sources(catalog)
        print(f"verified {len(verified)} source snapshots against the manifest")


if __name__ == "__main__":
    main()
