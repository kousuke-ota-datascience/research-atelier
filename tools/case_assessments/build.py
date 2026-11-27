#!/usr/bin/env python3
"""事例・ファクター評価を原文保持型JSONへ決定論的に変換する。

Review・Finalization済みの正本を入力とする任意の補助ツールであり、
canonical research chainの一部ではない。
Git checkout上でPython 3.10以上、jsonschema、リポジトリのsrcを使用する。
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

from jsonschema import Draft202012Validator

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "src"))
from research_atelier.reviewing.review_state import load_review_history
from research_atelier.validation.schema_validator import validate_data

FACTORS = re.compile(r"^(D\d{2}\.\d+) \[([CAPU])\] (.+)$")
CASE = re.compile(r"^### (C\d{2,}) (.+)（(SRC-\d{6}(?:、SRC-\d{6})*)）$")
SCOPE = re.compile(r"^(完全適合事例|近接事例|除外事例)(?:（([^）]+)）)?。根拠範囲：(K\d{4}(?:、K\d{4})*)。$")
AXIS = re.compile(r"^(D\d{2}\.\d+) ([^［]+)［([^］]+)］(.+)（(根拠|確認範囲)：(K\d{4}(?:、K\d{4})*)）$")
CRITERION = re.compile(r"^(R[1-4])［([^］]+)］(.+)（(K\d{4}(?:、K\d{4})*)）$")
FRAMEWORK_PIN = re.compile(r"(RQ-\d{6})のWorking Answer全(\d+)ファクターを固定記述軸とする。参照元: (INV-\d{6})/30_analysis\.json, commit ([0-9a-f]{40}), blob ([0-9a-f]{40})。")
FACTOR_STATUS = {
    "該当・原典報告": ("applicable", "reported"),
    "該当・分析上の推論": ("applicable", "inference"),
    "未知": ("undetermined", "undetermined"),
    "非該当": ("not_applicable", "not_applicable"),
    "サブタスク別：非該当／未知": ("mixed", "mixed"),
}
CRITERION_STATUS = {"確認済": "confirmed", "未確認": "unconfirmed", "不適合": "not_met"}
CASE_STATUS = {"完全適合事例": "full_match", "近接事例": "near_match", "除外事例": "excluded"}
LAYERS = ("00_context", "10_evidence", "20_synthesis", "30_analysis")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args], text=True, encoding="utf-8").strip()


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def serialize(data):
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


def unique_index(rows, key):
    result = {}
    for row in rows:
        ident = row[key]
        require(ident not in result, f"duplicate {key}: {ident}")
        result[ident] = row
    return result


def clean_committed(path):
    rel = path.relative_to(ROOT).as_posix()
    blob = git("hash-object", str(path))
    require(blob == git("rev-parse", f"HEAD:{rel}"), f"uncommitted input: {rel}")
    return blob


def review_gate(inv, base, context):
    require(context["context_state"] == "frozen", "context is not frozen")
    require(not git("status", "--porcelain", "--untracked-files=all", "--", str(base / "reviews")), "uncommitted Review history")
    history = load_review_history(inv, review_dir=base / "reviews", schema_path=ROOT / "schemas/v2")
    require(not history.issues and history.latest is not None, f"invalid Review history: {history.issues}")
    latest = history.latest
    require(latest["verdict"] == "PASS", "latest Review is not PASS")
    blobs = {k: clean_committed(base / f"{k}.json") for k in LAYERS}
    target = latest["target"]
    require(blobs == target["artifact_blob_shas"], "latest Review does not cover current canonical artifacts")
    for k, sha in blobs.items():
        path = (base / f"{k}.json").relative_to(ROOT).as_posix()
        require(git("rev-parse", f"{target['commit_sha']}:{path}") == sha, f"Review target mismatch: {k}")
    manifest_path = ROOT / latest["canonical_paths"]["manifest"]
    log_path = base / "projection_log_v2.json"
    log_blob = clean_committed(log_path)
    log = read_json(log_path)
    checked = validate_data(log, ROOT / "schemas/v2/projection_log.schema.json", artifact="projection_log_v2.json")
    require(checked.ok, "invalid projection log")
    require(log["result"] == "SUCCESS" and log["source_investigation_id"] == inv and log["rq_id"] == context["rq_id"] and log["target_rq_url"] == context["question"]["notion_url"], "finalization not current")
    analysis_commit = log["source_30_analysis_commit_sha"]
    analysis_rel = (base / "30_analysis.json").relative_to(ROOT).as_posix()
    require(git("rev-parse", f"{analysis_commit}:{analysis_rel}") == blobs["30_analysis"], "projection log points to stale analysis")
    return {
        "analysis_commit_sha": analysis_commit,
        "analysis_blob_sha": blobs["30_analysis"],
        "artifact_blob_shas": blobs,
        "review_seq": latest["review_seq"],
        "review_target_commit_sha": target["commit_sha"],
        "review_manifest_path": manifest_path.relative_to(ROOT).as_posix(),
        "review_manifest_blob_sha": clean_committed(manifest_path),
        "projection_log_blob_sha": log_blob,
    }


def load_framework(context):
    pins = [FRAMEWORK_PIN.fullmatch(x) for x in context["assumptions"]]
    pins = [m for m in pins if m]
    require(len(pins) == 1, "expected one explicit frozen framework pin")
    rq, count, inv, commit, blob = pins[0].groups()
    path = f"investigations/{inv}/30_analysis.json"
    require(git("rev-parse", f"{commit}:{path}") == blob, "framework blob mismatch")
    analysis = json.loads(git("show", f"{commit}:{path}"))
    require((analysis["rq_id"], analysis["investigation_id"]) == (rq, inv), "framework identity mismatch")
    definitions = []
    for line in analysis["working_answer"]["text"].splitlines():
        m = FACTORS.fullmatch(line)
        if m:
            ident, classification, definition = m.groups()
            definitions.append({"factor_id": ident, "framework_class": classification, "definition_text": definition})
    require(len(definitions) == int(count), "framework count mismatch")
    unique_index(definitions, "factor_id")
    return {"rq_id": rq, "investigation_id": inv, "analysis_commit_sha": commit, "analysis_blob_sha": blob, "factor_count": int(count), "factor_definitions": definitions}


def parse_criterion_definitions(text):
    m = re.search(r"^frozen Contextの4条件：(.*?)。確認済=", text, re.M)
    require(m is not None, "missing explicit four-criterion contract")
    segments = re.split(r"、(?=R[1-4]=)", m.group(1))
    rows = []
    for segment in segments:
        ident, definition = segment.split("=", 1)
        rows.append({"criterion_id": ident, "definition_text": definition})
    require([x["criterion_id"] for x in rows] == ["R1", "R2", "R3", "R4"], "criterion definitions mismatch")
    return rows


def lineage(refs, kus, evidence, sources):
    require(bool(refs) and len(refs) == len(set(refs)), "empty/duplicate K references")
    require(set(refs) <= kus.keys(), f"unknown K references: {refs}")
    evs = sorted({e for k in refs for e in kus[k]["evidence_refs"]})
    require(set(evs) <= evidence.keys(), f"unknown E references: {evs}")
    srcs = sorted({evidence[e]["provenance"]["source_id"] for e in evs})
    require(set(srcs) <= sources.keys(), f"unknown Source references: {srcs}")
    return {"knowledge_unit_refs": refs, "evidence_refs": evs, "source_refs": srcs}


def parse_cases(text, framework, kus, evidence, sources):
    expected = [x["factor_id"] for x in framework["factor_definitions"]]
    lines = text.splitlines()
    starts = [i for i, line in enumerate(lines) if line.startswith("### C")]
    require(bool(starts), "no case sections")
    cases = []
    for n, start in enumerate(starts):
        end = starts[n+1] if n+1 < len(starts) else len(lines)
        header = CASE.fullmatch(lines[start])
        require(header is not None, f"malformed case header at line {start+1}")
        cid, name, source_text = header.groups()
        declared = source_text.split("、")
        require(len(declared) == len(set(declared)) and set(declared) <= sources.keys(), f"{cid}: invalid case sources")
        body = [(i+1, lines[i]) for i in range(start+1, end) if lines[i].strip()]
        require(bool(body), f"{cid}: empty case")
        scope = SCOPE.fullmatch(body[0][1])
        require(scope is not None, f"{cid}: malformed scope")
        case_label, reason, scope_text = scope.groups()
        case_scope = lineage(scope_text.split("、"), kus, evidence, sources)
        require(set(case_scope["source_refs"]) == set(declared), f"{cid}: case scope/source mismatch")
        criteria, factors = [], []
        for line_no, raw in body[1:]:
            c, a = CRITERION.fullmatch(raw), AXIS.fullmatch(raw)
            if c:
                ident, label, description, ref_text = c.groups()
                require(label in CRITERION_STATUS, f"{cid}/{ident}: unknown criterion label")
                item = {"criterion_id": ident, "status": CRITERION_STATUS[label], "canonical_status": label, "assessment_text": description,
                        "reference_role": "confirmation_scope" if label == "未確認" else "basis",
                        "canonical_line": raw, "analysis_line": line_no}
                item.update(lineage(ref_text.split("、"), kus, evidence, sources))
                criteria.append(item)
            elif a:
                ident, label, status, description, role, ref_text = a.groups()
                require(status in FACTOR_STATUS, f"{cid}/{ident}: unknown factor label")
                applicability, epistemic = FACTOR_STATUS[status]
                require((role == "確認範囲") == (status == "未知"), f"{cid}/{ident}: reference role mismatch")
                item = {"factor_id": ident, "factor_label": label, "canonical_status": status,
                        "applicability": applicability, "epistemic_status": epistemic,
                        "value": description if applicability == "applicable" else None,
                        "assessment_text": description, "limitations": None,
                        "reference_role": "confirmation_scope" if role == "確認範囲" else "basis",
                        "canonical_line": raw, "analysis_line": line_no}
                item.update(lineage(ref_text.split("、"), kus, evidence, sources))
                factors.append(item)
            else:
                raise ValueError(f"{cid}: unparsed canonical line {line_no}: {raw[:120]}")
            require(set(item["knowledge_unit_refs"]) <= set(case_scope["knowledge_unit_refs"]), f"{cid}: row references outside case scope")
        require([x["criterion_id"] for x in criteria] == ["R1", "R2", "R3", "R4"], f"{cid}: missing, duplicate or reordered criteria")
        require([x["factor_id"] for x in factors] == expected, f"{cid}: missing, duplicate or reordered factors")
        eligibility = CASE_STATUS[case_label]
        require((eligibility == "full_match") == all(x["status"] == "confirmed" for x in criteria), f"{cid}: eligibility contradicts criteria")
        cases.append({"case_id": cid, "name": name, "source_refs": declared, "eligibility": eligibility,
                      "canonical_eligibility": case_label, "exclusion_reason": reason,
                      "knowledge_unit_scope": case_scope["knowledge_unit_refs"],
                      "canonical_header": lines[start], "canonical_scope_line": body[0][1],
                      "analysis_line": start+1, "criteria_assessments": criteria, "factor_assessments": factors})
    unique_index(cases, "case_id")
    return cases


def build(inv):
    require(re.fullmatch(r"INV-\d{6}", inv) is not None, "invalid Investigation ID")
    base = ROOT / "investigations" / inv
    context = read_json(base / "00_context.json")
    evidence = read_json(base / "10_evidence.json")
    synthesis = read_json(base / "20_synthesis.json")
    analysis = read_json(base / "30_analysis.json")
    require(all(x["investigation_id"] == inv and x["rq_id"] == context["rq_id"] for x in (context, evidence, synthesis, analysis)), "artifact identity mismatch")
    provenance = review_gate(inv, base, context)
    # 正本validatorの判定規則を再実装せず、既存の実装を利用する。
    subprocess.run([sys.executable, "-m", "research_atelier.validation.validate_investigation", inv, "--through", "30"], cwd=ROOT, env={**__import__("os").environ, "PYTHONPATH": str(ROOT / "src")}, check=True, stdout=sys.stderr)
    from category_adapter import PREFIX, build_category_contract
    from grinding_adapter import PREFIX as GRINDING_PREFIX, build_grinding_contract
    category_contract = [x for x in context["assumptions"] if x.startswith(PREFIX)]
    grinding_contract = [x for x in context["assumptions"] if x.startswith(GRINDING_PREFIX)]
    external_contract = [x for x in context["assumptions"] if FRAMEWORK_PIN.fullmatch(x)]
    require(sum(bool(x) for x in (category_contract, grinding_contract, external_contract)) == 1, "missing or ambiguous case contract")
    if grinding_contract:
        data = build_grinding_contract(context, analysis, provenance,
            unique_index(synthesis["knowledge_units"], "knowledge_unit_id"),
            unique_index(evidence["evidence_items"], "evidence_id"),
            unique_index(evidence["sources"], "source_id"), require=require, lineage=lineage)
        Draft202012Validator(read_json(HERE / "case_assessments.grinding.schema.json")).validate(data)
        return data
    if category_contract:
        data = build_category_contract(context, analysis, provenance,
            unique_index(synthesis["knowledge_units"], "knowledge_unit_id"),
            unique_index(evidence["evidence_items"], "evidence_id"),
            unique_index(evidence["sources"], "source_id"), require=require, lineage=lineage)
        Draft202012Validator(read_json(HERE / "case_assessments.categories.schema.json")).validate(data)
        return data
    framework = load_framework(context)
    text = analysis["working_answer"]["text"]
    criteria_defs = parse_criterion_definitions(text)
    cases = parse_cases(text, framework, unique_index(synthesis["knowledge_units"], "knowledge_unit_id"),
                        unique_index(evidence["evidence_items"], "evidence_id"), unique_index(evidence["sources"], "source_id"))
    factors = [row for case in cases for row in case["factor_assessments"]]
    criteria = [row for case in cases for row in case["criteria_assessments"]]
    data = {"schema_version": "1.0.0", "artifact_type": "case_assessments", "authority": "derived",
            "investigation_id": inv, "rq_id": context["rq_id"], "derived_from": provenance,
            "factor_framework": framework, "criteria_definitions": criteria_defs,
            "summary": {"case_count": len(cases), "factor_assessment_count": len(factors),
                        "criterion_assessment_count": len(criteria),
                        "eligibility_counts": dict(sorted(Counter(c["eligibility"] for c in cases).items())),
                        "factor_status_counts": dict(sorted(Counter(r["canonical_status"] for r in factors).items())),
                        "criterion_status_counts": dict(sorted(Counter(r["status"] for r in criteria).items()))},
            "cases": cases}
    Draft202012Validator(read_json(HERE / "case_assessments.schema.json")).validate(data)
    return data


def check_overlay(overlay, baseline, baseline_bytes):
    Draft202012Validator(read_json(HERE / "semantic_overlay.schema.json")).validate(overlay)
    require(overlay["baseline_sha256"] == hashlib.sha256(baseline_bytes).hexdigest(), "overlay pins a different baseline")
    require(overlay["investigation_id"] == baseline["investigation_id"] and overlay["rq_id"] == baseline["rq_id"], "overlay identity mismatch")
    index = {(c["case_id"], a["factor_id"]): a for c in baseline["cases"] for a in c["factor_assessments"]}
    seen = set()
    for entry in overlay["entries"]:
        key = (entry["case_id"], entry["factor_id"])
        require(key in index and key not in seen, f"unknown or duplicate overlay entry {key}")
        seen.add(key)
        row = index[key]
        for item in entry["attributes"]:
            quote = item["source_excerpt"]
            require(quote in row["assessment_text"], f"{key}: unsupported excerpt")
            require(item["value_text"] in quote, f"{key}: value not present in excerpt")
            if item["unit"] is not None:
                require(item["unit"] in quote, f"{key}: unit not present in excerpt")
        for quote in entry["limitations"]:
            require(quote in row["assessment_text"], f"{key}: unsupported limitation")
    # 原文抜粋の一致は意味論的妥当性を保証しない。自動統合は行わない。


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("investigation_id")
    parser.add_argument("--check", action="store_true", help="保存済みの派生成果物と再生成結果の完全一致を検証する")
    parser.add_argument("--overlay", type=Path, help="任意の独立したsemantic overlayを検証する（--checkを含む）")
    parser.add_argument("--stdout", action="store_true", help="ファイルに書き込まず、生成したJSONを標準出力に出力する")
    args = parser.parse_args()
    data = build(args.investigation_id)
    content = serialize(data)
    out = ROOT / "investigations" / args.investigation_id / "derived" / "case_assessments.json"
    if args.check or args.overlay:
        require(out.read_bytes() == content.encode("utf-8"), "stored derivative differs from regenerated result")
        if args.overlay:
            check_overlay(read_json(args.overlay), data, out.read_bytes())
        print("PASS: derivative matches exact regeneration" + ("; overlay anchors valid (semantic review still required)" if args.overlay else ""), file=sys.stderr)
    elif args.stdout:
        sys.stdout.write(content)
    else:
        out.parent.mkdir(parents=True, exist_ok=True)
        tmp = out.with_suffix(".json.tmp")
        tmp.write_bytes(content.encode("utf-8"))
        tmp.replace(out)
        print(f"Generated {out.relative_to(ROOT)}", file=sys.stderr)
    print(json.dumps(data["summary"], ensure_ascii=False), file=sys.stderr)


if __name__ == "__main__":
    main()
