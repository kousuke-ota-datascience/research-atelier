"""Read-only Git facts for canonical lore artifacts."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess

ARTICLE_ROOT = Path(__file__).resolve().parents[2]
CANONICAL_ROOT = ARTICLE_ROOT / "docs/10_each_lore"
ARTIFACT_SUFFIXES = {"00": "00_sources", "10": "10_contents", "20": "20_analysis"}


@dataclass(frozen=True)
class GitArtifactState:
    artifact: str
    path: Path
    exists: bool
    commit_sha: str | None
    blob_sha: str | None


@dataclass(frozen=True)
class GitSnapshot:
    entry_id: str
    repository_root: Path
    artifacts: dict[str, GitArtifactState]


def _run(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=check,
    )


def repository_root() -> Path:
    proc = _run(ARTICLE_ROOT, "rev-parse", "--show-toplevel")
    return Path(proc.stdout.strip()).resolve()


def resolve_artifact_path(entry_id: str, artifact: str) -> Path:
    suffix = ARTIFACT_SUFFIXES[artifact]
    matches = sorted(CANONICAL_ROOT.glob(f"*/{entry_id}_{suffix}.json"))
    matches = [p for p in matches if "0000_tutorial" not in p.parts]
    if len(matches) > 1:
        raise RuntimeError(f"artifact path ambiguity for {entry_id}/{artifact}: {matches}")
    if len(matches) == 1:
        return matches[0]
    dirs = sorted(p for p in CANONICAL_ROOT.glob(f"{entry_id}*") if p.is_dir() and p.name != "0000_tutorial")
    if len(dirs) > 1:
        raise RuntimeError(f"entry directory ambiguity for {entry_id}: {dirs}")
    if len(dirs) == 1:
        return dirs[0] / f"{entry_id}_{suffix}.json"
    return CANONICAL_ROOT / entry_id / f"{entry_id}_{suffix}.json"


def load_entry_git_state(entry_id: str) -> GitSnapshot:
    repo = repository_root()
    artifacts: dict[str, GitArtifactState] = {}
    for artifact in ("00", "10", "20"):
        path = resolve_artifact_path(entry_id, artifact)
        if not path.is_file():
            artifacts[artifact] = GitArtifactState(artifact, path, False, None, None)
            continue
        rel = path.resolve().relative_to(repo).as_posix()
        log = _run(repo, "log", "-n", "1", "--format=%H", "--", rel)
        commit = log.stdout.strip() or None
        if commit is None:
            artifacts[artifact] = GitArtifactState(artifact, path, True, None, None)
            continue
        blob = _run(repo, "rev-parse", f"{commit}:{rel}").stdout.strip()
        artifacts[artifact] = GitArtifactState(artifact, path, True, commit, blob)
    return GitSnapshot(entry_id, repo, artifacts)


def compare_commits(left_sha: str | None, right_sha: str | None, *, repo: Path | None = None) -> str:
    """Return exact/left_ancestor/right_ancestor/diverged/missing."""
    if not left_sha or not right_sha:
        return "missing"
    if left_sha == right_sha:
        return "exact"
    repo = repo or repository_root()
    for sha in (left_sha, right_sha):
        if _run(repo, "cat-file", "-e", f"{sha}^{{commit}}", check=False).returncode != 0:
            return "missing"
    if _run(repo, "merge-base", "--is-ancestor", left_sha, right_sha, check=False).returncode == 0:
        return "left_ancestor"
    if _run(repo, "merge-base", "--is-ancestor", right_sha, left_sha, check=False).returncode == 0:
        return "right_ancestor"
    return "diverged"
