"""Deterministic structural validation of D01-D21 taxonomy references."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .schema_validator import ValidationIssue

DIMENSIONS = tuple(f"D{i:02d}" for i in range(1, 22))
CATALOG_RELATIVE_PATH = Path("docs/00_research_overview/taxonomy_catalog.json")


def load_taxonomy_catalog(article_root: Path) -> Mapping[str, Any]:
    path = article_root / CATALOG_RELATIVE_PATH
    if not path.is_file():
        raise FileNotFoundError(f"machine-readable taxonomy catalog not found: {path}")

    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"taxonomy catalog must be an object: {path}")
    if not isinstance(data.get("catalog_version"), str) or not data["catalog_version"]:
        raise ValueError(f"taxonomy catalog must contain non-empty catalog_version: {path}")

    dimensions = data.get("dimensions")
    if not isinstance(dimensions, dict) or sorted(dimensions) != list(DIMENSIONS):
        raise ValueError(f"taxonomy catalog dimensions must be exactly D01-D21: {path}")

    codes = data.get("codes")
    if not isinstance(codes, dict):
        raise ValueError(f"taxonomy catalog must contain object 'codes': {path}")

    for key, record in codes.items():
        if not isinstance(record, dict):
            raise ValueError(f"taxonomy code record must be an object: {key}")
        code_id = record.get("code_id")
        dimension = record.get("dimension")
        parent_id = record.get("parent_id")
        if code_id != key:
            raise ValueError(f"taxonomy code_id must match map key: {key}")
        if dimension not in DIMENSIONS:
            raise ValueError(f"taxonomy code has invalid dimension: {key} -> {dimension}")
        if not code_id.startswith(dimension + "."):
            raise ValueError(f"taxonomy code does not belong to declared dimension: {key} -> {dimension}")
        if parent_id is not None:
            if not isinstance(parent_id, str) or not parent_id.startswith(dimension + "."):
                raise ValueError(f"taxonomy code has invalid parent_id: {key} -> {parent_id}")
            if not code_id.startswith(parent_id + "."):
                raise ValueError(f"taxonomy parent_id is not a prefix of code_id: {key} -> {parent_id}")

    return data


def _issue(rule: str, path: str, message: str, *, expected=None, actual=None) -> ValidationIssue:
    return ValidationIssue(rule, "20", path, message, "taxonomy_validator", expected, actual)


def validate_taxonomy(analysis: Mapping[str, Any], taxonomy_catalog: Mapping[str, Any]) -> tuple[ValidationIssue, ...]:
    errors: list[ValidationIssue] = []
    dimensions = analysis.get("dimensions", [])
    ids = [d.get("dimension_id") for d in dimensions if isinstance(d, dict)]
    if sorted(ids) != list(DIMENSIONS):
        errors.append(
            _issue(
                "V-DIM-001",
                "$.dimensions",
                "dimension set must be exactly D01-D21",
                expected=list(DIMENSIONS),
                actual=ids,
            )
        )

    codes: Mapping[str, Any] = taxonomy_catalog.get("codes", {})
    for idx, dim in enumerate(dimensions):
        if not isinstance(dim, dict):
            continue

        dim_id = dim.get("dimension_id")
        status = dim.get("status")
        primary = dim.get("primary")
        secondary = dim.get("secondary", [])

        taxonomy_gap = dim.get("taxonomy_gap")
        has_explicit_gap = (
            isinstance(taxonomy_gap, dict)
            and taxonomy_gap.get("present") is True
        )

        if status in {"D", "I"} and not isinstance(primary, dict) and not has_explicit_gap:
            errors.append(
                _issue(
                    "V-STATUS-001",
                    f"$.dimensions[{idx}].primary",
                    f"status {status} requires primary code unless taxonomy_gap.present=true",
                )
            )
        if status in {"U", "NA", "C"} and (primary is not None or secondary):
            errors.append(
                _issue(
                    "V-STATUS-001",
                    f"$.dimensions[{idx}]",
                    f"status {status} forbids primary/secondary codes",
                )
            )

        refs: list[tuple[str, Mapping[str, Any]]] = []
        if isinstance(primary, dict):
            refs.append(("primary", primary))
        refs.extend(
            (f"secondary[{secondary_idx}]", ref)
            for secondary_idx, ref in enumerate(secondary)
            if isinstance(ref, dict)
        )

        for ref_name, ref in refs:
            ref_path = f"$.dimensions[{idx}].{ref_name}"
            code_id = ref.get("code_id")
            cat = codes.get(code_id)
            if not isinstance(cat, dict):
                errors.append(_issue("V-CODE-001", ref_path + ".code_id", f"unknown code_id: {code_id}"))
                continue

            expected_parent = cat.get("parent_id")
            actual_parent = ref.get("parent_id")
            if actual_parent != expected_parent:
                errors.append(
                    _issue(
                        "V-PARENT-001",
                        ref_path + ".parent_id",
                        f"parent mismatch for {code_id}",
                        expected=expected_parent,
                        actual=actual_parent,
                    )
                )

            expected_dimension = cat.get("dimension")
            if dim_id != expected_dimension:
                errors.append(
                    _issue(
                        "V-CODE-002",
                        ref_path + ".code_id",
                        f"code {code_id} does not belong to {dim_id}",
                        expected=dim_id,
                        actual=expected_dimension,
                    )
                )

    return tuple(sorted(errors, key=ValidationIssue.sort_key))
