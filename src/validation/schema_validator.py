"""Deterministic JSON parsing and JSON Schema validation."""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker, RefResolver
from jsonschema.exceptions import SchemaError


@dataclass(frozen=True)
class ValidationIssue:
    rule_id: str
    artifact: str
    json_path: str
    message: str
    validator: str = "schema_validator"
    expected: Any | None = None
    actual: Any | None = None

    def sort_key(self) -> tuple[str, str, str, str]:
        return (self.artifact, self.json_path, self.rule_id, self.message)


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    data: Any | None
    errors: tuple[ValidationIssue, ...]


def _json_path(parts: list[Any]) -> str:
    if not parts:
        return "$"
    out = "$"
    for part in parts:
        if isinstance(part, int):
            out += f"[{part}]"
        else:
            out += "." + str(part)
    return out


def validate_data(
    data: Any,
    schema_path: str | Path,
    *,
    artifact: str = "data",
) -> ValidationResult:
    """Validate already-parsed data against one JSON Schema."""
    schema_path = Path(schema_path)
    errors: list[ValidationIssue] = []

    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        errors.append(ValidationIssue("V-SCHEMA-000", artifact, "$", f"schema load failed: {exc}"))
        return ValidationResult(False, data, tuple(errors))

    try:
        base_uri = schema_path.resolve().parent.as_uri() + "/"
        resolver = RefResolver(base_uri=base_uri, referrer=schema)
        validator = Draft202012Validator(schema, resolver=resolver, format_checker=FormatChecker())
        schema_errors = sorted(
            validator.iter_errors(data),
            key=lambda e: (_json_path(list(e.absolute_path)), str(e.validator), e.message),
        )
    except (SchemaError, OSError, ValueError) as exc:
        errors.append(ValidationIssue("V-SCHEMA-000", artifact, "$", f"schema configuration failed: {exc}"))
        return ValidationResult(False, data, tuple(errors))

    for err in schema_errors:
        errors.append(
            ValidationIssue(
                "V-SCHEMA-001",
                artifact,
                _json_path(list(err.absolute_path)),
                err.message,
                expected=err.validator_value,
                actual=err.instance,
            )
        )

    errors.sort(key=ValidationIssue.sort_key)
    return ValidationResult(not errors, data, tuple(errors))


def validate_artifact(
    artifact_path: str | Path,
    schema_path: str | Path,
    *,
    artifact: str | None = None,
) -> ValidationResult:
    artifact_path = Path(artifact_path)
    label = artifact or artifact_path.stem

    if not artifact_path.is_file():
        issue = ValidationIssue("V-PARSE-001", label, "$", f"file not found: {artifact_path}")
        return ValidationResult(False, None, (issue,))

    try:
        data = json.loads(artifact_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        issue = ValidationIssue("V-PARSE-001", label, "$", f"JSON parse failed: {exc}")
        return ValidationResult(False, None, (issue,))

    return validate_data(data, schema_path, artifact=label)
