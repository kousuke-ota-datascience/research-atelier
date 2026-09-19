"""Optional token-based CLI adapter for deterministic control-plane synchronization."""
from __future__ import annotations

import argparse
import json
import sys

from .git_state import compare_commits, load_entry_git_state
from .notion_controlplane import apply_mutations, load_entry_state
from .reconcile import reconcile
from .review_state import load_entry_review_state


def _relations(cp, git, reviews) -> dict[tuple[str, str], str]:
    facts: dict[tuple[str, str], str] = {}
    for artifact in ("00", "10", "20"):
        g = git.artifacts.get(artifact)
        if g is None or not g.commit_sha:
            continue
        c = cp.artifacts.get(artifact)
        if c and c.post_sha:
            facts[("cp_post", artifact)] = compare_commits(c.post_sha, g.commit_sha, repo=git.repository_root)
        r = reviews.latest.get(artifact)
        if r:
            facts[("review_target", artifact)] = compare_commits(r.target_commit_sha, g.commit_sha, repo=git.repository_root)
    return facts


def sync_controlplane(entry_id: str) -> dict:
    try:
        cp = load_entry_state(entry_id)
        git = load_entry_git_state(entry_id)
        reviews = load_entry_review_state(entry_id)
        result = reconcile(cp, git, reviews, _relations(cp, git, reviews))
        base = {
            "entry_id": entry_id,
            "reason_code": result.issues[0] if result.issues else None,
            "changed_artifacts": [],
            "messages": [result.summary, *result.issues],
            "mutation_count": len(result.mutations),
            "verified": False,
        }
        if result.outcome == "BLOCKED":
            return {**base, "result": "BLOCKED"}
        if result.outcome == "ERROR":
            return {**base, "result": "ERROR"}
        if result.outcome == "NOOP":
            return {**base, "result": "PASS", "verified": True}

        applied = apply_mutations(result.mutations, cp)
        if not applied.success:
            return {**base, "result": "ERROR", "reason_code": applied.error, "messages": [result.summary, applied.error or "mutation failed"]}

        after = load_entry_state(entry_id)
        if after.issues:
            return {**base, "result": "ERROR", "reason_code": "post_update_snapshot_invalid", "messages": [*after.issues]}
        for mutation in result.mutations:
            row = after.artifacts[mutation.artifact]
            values = {
                "Status": row.status,
                "最新レビュー版": row.latest_review_seq,
                "pre-SHA": row.pre_sha,
                "post-SHA": row.post_sha,
                "remarks": row.remarks,
            }
            for key, expected in mutation.changes.items():
                if values.get(key) != expected:
                    return {**base, "result": "ERROR", "reason_code": "post_update_verification_error", "messages": [f"{mutation.artifact}:{key} expected {expected!r}, got {values.get(key)!r}"]}
        return {
            **base,
            "result": "UPDATED",
            "changed_artifacts": list(applied.updated_artifacts),
            "verified": True,
        }
    except Exception as exc:
        return {
            "entry_id": entry_id,
            "result": "ERROR",
            "reason_code": type(exc).__name__,
            "changed_artifacts": [],
            "messages": [str(exc)],
            "mutation_count": 0,
            "verified": False,
        }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("entry_id", help="four-digit Entry_ID")
    args = parser.parse_args(argv)
    if not (len(args.entry_id) == 4 and args.entry_id.isdigit()):
        parser.error("entry_id must be four digits")
    result = sync_controlplane(args.entry_id)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["result"] in {"PASS", "UPDATED"} else 1 if result["result"] == "BLOCKED" else 2


if __name__ == "__main__":
    sys.exit(main())
