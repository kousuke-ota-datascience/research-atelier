"""Notion I/O for the lore-entry control plane only."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from typing import Any, Iterable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DEFAULT_DATA_SOURCE_ID = "3dee5855-be39-807e-90c7-000bb6d72cd3"
NOTION_VERSION = os.environ.get("NOTION_VERSION", "2025-09-03")
ALLOWED_STATUSES = frozenset(
    {"未", "レビュー待", "要修正", "再作業中", "再レビュー待", "完了", "－（対象外）"}
)

# Current production names are pre/post-commitSHA. The aliases keep the
# implementation compatible with the redesigned pre/post-SHA naming without
# making the I/O layer reinterpret domain semantics.
PROPERTY_NAMES = {
    "Status": os.environ.get("CONTROLPLANE_STATUS_PROPERTY", "Status"),
    "最新レビュー版": os.environ.get("CONTROLPLANE_REVIEW_SEQ_PROPERTY", "最新レビュー版"),
    "pre-SHA": os.environ.get("CONTROLPLANE_PRE_SHA_PROPERTY", "pre-commitSHA"),
    "post-SHA": os.environ.get("CONTROLPLANE_POST_SHA_PROPERTY", "post-commitSHA"),
    "remarks": os.environ.get("CONTROLPLANE_REMARKS_PROPERTY", "remarks"),
}


@dataclass(frozen=True)
class ControlPlaneArtifact:
    row_id: str
    entry_id: str
    artifact: str
    status: str | None
    latest_review_seq: int | None
    pre_sha: str | None
    post_sha: str | None
    remarks: str | None
    fingerprint: str


@dataclass(frozen=True)
class ControlPlaneSnapshot:
    entry_id: str
    artifacts: dict[str, ControlPlaneArtifact]
    issues: tuple[str, ...]


@dataclass(frozen=True)
class ApplyResult:
    success: bool
    updated_artifacts: tuple[str, ...]
    error: str | None = None


def _token() -> str:
    token = os.environ.get("NOTION_TOKEN") or os.environ.get("NOTION_API_TOKEN")
    if not token:
        raise RuntimeError("NOTION_TOKEN (or NOTION_API_TOKEN) is required")
    return token


def _request(method: str, path: str, payload: dict | None = None) -> dict:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    req = Request(
        "https://api.notion.com" + path,
        data=body,
        method=method,
        headers={
            "Authorization": f"Bearer {_token()}",
            "Notion-Version": NOTION_VERSION,
            "Content-Type": "application/json",
        },
    )
    try:
        with urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError) as exc:
        raise RuntimeError(f"Notion {method} {path} failed: {exc}") from exc


def _plain(prop: Any) -> Any:
    if not isinstance(prop, dict):
        return None
    ptype = prop.get("type")
    if ptype in {"title", "rich_text"}:
        return "".join(x.get("plain_text", "") for x in prop.get(ptype, [])) or None
    if ptype in {"select", "status"}:
        value = prop.get(ptype)
        return value.get("name") if isinstance(value, dict) else None
    if ptype == "number":
        return prop.get("number")
    if ptype == "formula":
        value = prop.get("formula", {})
        return value.get(value.get("type"))
    return prop.get(ptype)


def _prop(props: dict, logical_name: str) -> Any:
    """Read a logical property using configured current physical name."""
    return props.get(PROPERTY_NAMES[logical_name])


def _fingerprint(row: dict) -> str:
    props = row.get("properties", {})
    normalized = {
        "Entry_ID": _plain(props.get("Entry_ID")),
        "成果物": _plain(props.get("成果物")),
        **{logical: _plain(_prop(props, logical)) for logical in PROPERTY_NAMES},
        "last_edited_time": row.get("last_edited_time"),
    }
    return hashlib.sha256(
        json.dumps(normalized, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()


def _list_rows() -> list[dict]:
    ds = os.environ.get(
        "NOTION_CONTROLPLANE_DATA_SOURCE_ID", DEFAULT_DATA_SOURCE_ID
    ).replace("-", "")
    results: list[dict] = []
    cursor: str | None = None
    while True:
        payload: dict[str, Any] = {"page_size": 100}
        if cursor:
            payload["start_cursor"] = cursor
        page = _request("POST", f"/v1/data_sources/{ds}/query", payload)
        results.extend(page.get("results", []))
        if not page.get("has_more"):
            break
        cursor = page.get("next_cursor")
    return results


def load_entry_state(entry_id: str) -> ControlPlaneSnapshot:
    rows = []
    for row in _list_rows():
        props = row.get("properties", {})
        if str(_plain(props.get("Entry_ID")) or "") == entry_id:
            rows.append(row)

    artifacts: dict[str, ControlPlaneArtifact] = {}
    issues: list[str] = []
    for row in rows:
        props = row.get("properties", {})
        artifact = str(_plain(props.get("成果物")) or "")
        if artifact not in {"00", "10", "20"}:
            issues.append(f"invalid_artifact_value:{artifact or '<empty>'}")
            continue
        if artifact in artifacts:
            issues.append(f"duplicate_logical_key:{entry_id}:{artifact}")
            continue

        status = _plain(_prop(props, "Status"))
        if status not in ALLOWED_STATUSES:
            issues.append(f"invalid_status_value:{artifact}:{status!r}")

        latest = _plain(_prop(props, "最新レビュー版"))
        try:
            latest_int = int(latest) if latest not in (None, "") else None
        except (TypeError, ValueError):
            issues.append(f"invalid_latest_review_seq:{artifact}:{latest}")
            latest_int = None

        artifacts[artifact] = ControlPlaneArtifact(
            row_id=row["id"],
            entry_id=entry_id,
            artifact=artifact,
            status=status,
            latest_review_seq=latest_int,
            pre_sha=_plain(_prop(props, "pre-SHA")),
            post_sha=_plain(_prop(props, "post-SHA")),
            remarks=_plain(_prop(props, "remarks")),
            fingerprint=_fingerprint(row),
        )

    for artifact in ("00", "10", "20"):
        if artifact not in artifacts:
            issues.append(f"missing_row:{entry_id}:{artifact}")
    return ControlPlaneSnapshot(entry_id, artifacts, tuple(sorted(set(issues))))


def _text_payload(value: Any) -> dict:
    if value is None:
        return {"rich_text": []}
    return {"rich_text": [{"type": "text", "text": {"content": str(value)}}]}


def _property_payload(logical_name: str, value: Any) -> dict:
    # Actual current DB: Status=select, review seq=text, SHA/remarks=text.
    if logical_name == "Status":
        if value not in ALLOWED_STATUSES:
            raise ValueError(f"invalid Status mutation: {value!r}")
        return {"select": {"name": str(value)}}
    if logical_name == "最新レビュー版":
        return _text_payload(value)
    return _text_payload(value)


def apply_mutations(
    mutations: Iterable[Any], expected_snapshot: ControlPlaneSnapshot
) -> ApplyResult:
    mutations = tuple(mutations)
    if not mutations:
        return ApplyResult(True, ())

    current = load_entry_state(expected_snapshot.entry_id)
    if current.issues:
        return ApplyResult(False, (), f"current control plane invalid: {current.issues}")

    for mutation in mutations:
        expected = expected_snapshot.artifacts.get(mutation.artifact)
        actual = current.artifacts.get(mutation.artifact)
        if (
            expected is None
            or actual is None
            or expected.fingerprint != actual.fingerprint
        ):
            return ApplyResult(False, (), f"concurrent_update:{mutation.artifact}")

    updated: list[str] = []
    try:
        for mutation in mutations:
            row = current.artifacts[mutation.artifact]
            props = {
                PROPERTY_NAMES[logical]: _property_payload(logical, value)
                for logical, value in mutation.changes.items()
                if logical in PROPERTY_NAMES
            }
            if not props:
                continue
            _request("PATCH", f"/v1/pages/{row.row_id}", {"properties": props})
            updated.append(mutation.artifact)
    except Exception as exc:
        return ApplyResult(False, tuple(updated), f"notion_write_error:{exc}")
    return ApplyResult(True, tuple(updated))
