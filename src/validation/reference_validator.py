"""Cross-file identity and reference validation for one lore entry."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .schema_validator import ValidationIssue

SUPPORTED_SCHEMA_VERSIONS = {"1.0"}


@dataclass(frozen=True)
class ParsedArtifact:
    artifact: str
    path: Path
    data: Mapping[str, Any]


def _issue(rule: str, artifact: str, path: str, message: str, *, expected=None, actual=None) -> ValidationIssue:
    return ValidationIssue(rule, artifact, path, message, "reference_validator", expected, actual)


def _duplicates(values: list[str]) -> set[str]:
    seen: set[str] = set()
    dup: set[str] = set()
    for value in values:
        if value in seen:
            dup.add(value)
        seen.add(value)
    return dup


def validate_references(entry_id: str, artifacts: Mapping[str, ParsedArtifact]) -> tuple[ValidationIssue, ...]:
    errors: list[ValidationIssue] = []

    for artifact in ("00", "10", "20"):
        doc = artifacts.get(artifact)
        if doc is None:
            continue
        data = doc.data
        actual_entry = data.get("entry_id")
        if actual_entry != entry_id:
            errors.append(_issue("V-ENTRY-001", artifact, "$.entry_id", "entry_id mismatch", expected=entry_id, actual=actual_entry))
        if not doc.path.name.startswith(f"{entry_id}_"):
            errors.append(_issue("V-ENTRY-002", artifact, "$", f"filename does not start with {entry_id}_"))
        if data.get("schema_version") not in SUPPORTED_SCHEMA_VERSIONS:
            errors.append(_issue("V-VERSION-001", artifact, "$.schema_version", "unsupported schema_version", expected=sorted(SUPPORTED_SCHEMA_VERSIONS), actual=data.get("schema_version")))

    source_ids: set[str] = set()
    evidence_ids: set[str] = set()
    content_ids: set[str] = set()
    variant_ids: set[str] = set()

    a00 = artifacts.get("00")
    if a00:
        sources = a00.data.get("sources", [])
        evidence = a00.data.get("evidence", [])
        svals = [x.get("source_id") for x in sources if isinstance(x, dict) and isinstance(x.get("source_id"), str)]
        evals = [x.get("evidence_id") for x in evidence if isinstance(x, dict) and isinstance(x.get("evidence_id"), str)]
        for value in sorted(_duplicates(svals)):
            errors.append(_issue("V-ID-001", "00", "$.sources", f"duplicate source_id: {value}"))
        for value in sorted(_duplicates(evals)):
            errors.append(_issue("V-ID-001", "00", "$.evidence", f"duplicate evidence_id: {value}"))
        source_ids.update(svals)
        evidence_ids.update(evals)
        for idx, ev in enumerate(evidence):
            if not isinstance(ev, dict):
                continue
            sid = ev.get("source_id")
            if isinstance(sid, str) and sid not in source_ids:
                errors.append(_issue("V-REF-001", "00", f"$.evidence[{idx}].source_id", f"dangling source reference: {sid}"))

    a10 = artifacts.get("10")
    if a10:
        units = a10.data.get("content_units", [])
        variants = a10.data.get("variants", [])
        cvals = [x.get("content_id") for x in units if isinstance(x, dict) and isinstance(x.get("content_id"), str)]
        vvals = [x.get("variant_id") for x in variants if isinstance(x, dict) and isinstance(x.get("variant_id"), str)]
        for value in sorted(_duplicates(cvals)):
            errors.append(_issue("V-ID-001", "10", "$.content_units", f"duplicate content_id: {value}"))
        for value in sorted(_duplicates(vvals)):
            errors.append(_issue("V-ID-001", "10", "$.variants", f"duplicate variant_id: {value}"))
        content_ids.update(cvals)
        variant_ids.update(vvals)

        summary = a10.data.get("summary", {})
        if isinstance(summary, dict):
            for ref in summary.get("coverage_refs", []):
                if ref not in content_ids:
                    errors.append(
                        _issue(
                            "V-REF-001",
                            "10",
                            "$.summary.coverage_refs",
                            f"dangling content reference: {ref}",
                        )
                    )

        if a00:
            for idx, unit in enumerate(units):
                if isinstance(unit, dict):
                    for ref in unit.get("evidence_refs", []):
                        if ref not in evidence_ids:
                            errors.append(_issue("V-REF-001", "10", f"$.content_units[{idx}].evidence_refs", f"dangling evidence reference: {ref}"))
            for idx, variant in enumerate(variants):
                if not isinstance(variant, dict):
                    continue
                for ref in variant.get("evidence_refs", []):
                    if ref not in evidence_ids:
                        errors.append(_issue("V-REF-001", "10", f"$.variants[{idx}].evidence_refs", f"dangling evidence reference: {ref}"))
                for ref in variant.get("content_refs", []):
                    if ref not in content_ids:
                        errors.append(_issue("V-REF-001", "10", f"$.variants[{idx}].content_refs", f"dangling content reference: {ref}"))
            for idx, item in enumerate(a10.data.get("uncertainties", [])):
                if not isinstance(item, dict):
                    continue
                for ref in item.get("evidence_refs", []):
                    if ref not in evidence_ids:
                        errors.append(_issue("V-REF-001", "10", f"$.uncertainties[{idx}].evidence_refs", f"dangling evidence reference: {ref}"))
                for ref in item.get("content_refs", []):
                    if ref not in content_ids:
                        errors.append(_issue("V-REF-001", "10", f"$.uncertainties[{idx}].content_refs", f"dangling content reference: {ref}"))

    a20 = artifacts.get("20")
    if a20 and a10:
        scope = a20.data.get("version_scope", {})
        if isinstance(scope, dict):
            for key in ("included_variants", "excluded_variants"):
                for ref in scope.get(key, []):
                    if ref not in variant_ids:
                        errors.append(_issue("V-REF-001", "20", f"$.version_scope.{key}", f"dangling variant reference: {ref}"))
            for ref in scope.get("content_refs", []):
                if ref not in content_ids:
                    errors.append(_issue("V-REF-001", "20", "$.version_scope.content_refs", f"dangling content reference: {ref}"))
        for idx, dim in enumerate(a20.data.get("dimensions", [])):
            if not isinstance(dim, dict):
                continue
            for ref in dim.get("content_refs", []):
                if ref not in content_ids:
                    errors.append(_issue("V-REF-001", "20", f"$.dimensions[{idx}].content_refs", f"dangling content reference: {ref}"))
            if a00:
                for ref in dim.get("evidence_refs", []):
                    if ref not in evidence_ids:
                        errors.append(_issue("V-REF-001", "20", f"$.dimensions[{idx}].evidence_refs", f"dangling evidence reference: {ref}"))

    return tuple(sorted(errors, key=ValidationIssue.sort_key))
