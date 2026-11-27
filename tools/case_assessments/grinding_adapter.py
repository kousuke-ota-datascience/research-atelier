"""研削品質保証・状態基準保全の明示契約を原文保持で抽出する (v3)。

R判定はcase scope、D記述はcategory scope。カテゴリ内の個別属性の
認識状態や適用可否を生成器で推定しない。
"""
from __future__ import annotations

from collections import Counter
import re
from category_adapter import parse_refs, STATUS, HEADER

PREFIX = "固定記述軸は合意済みの10カテゴリとする。"
CATEGORY_IDS = [f"D{i:02d}" for i in range(1, 11)]
CRITERION_IDS = ["R1", "R2", "R3", "R4-A", "R5-A", "R4-B", "R5-B"]
INCLUDE_IDS = ["R1", "R2", "R3", "R4-A", "R4-B", "R5-A", "R5-B"]
ELIGIBILITY = {
    "統合型": "integrated", "品質保証型": "quality_assurance",
    "状態基準保全型": "condition_based_maintenance",
    "品質推定事例": "quality_estimation", "近接事例": "near_match", "除外事例": "excluded",
}
SCOPE = re.compile(r"^- 採択区分：(.+)（(K\d{4}[^（）]*)）$")
AXIS = re.compile(r"^- (D\d{2}) ([^：]+)：(.+)（(K\d{4}[^（）]*)）$")
REASON = "- 判定理由（分析上の推論）："


def definitions(context, require):
    rows = [x for x in context["assumptions"] if x.startswith(PREFIX)]
    require(len(rows) == 1, "expected one grinding category contract")
    raw = rows[0]
    m = re.fullmatch(re.escape(PREFIX) + r"(.+?)。各事例に全10カテゴリを記述し、.+", raw)
    require(m is not None, "malformed grinding framework")
    factors = []
    for segment in m.group(1).split("。"):
        match = re.fullmatch(r"(D\d{2}) ([^（]+)（([^）]+)）", segment)
        require(match is not None, f"invalid category definition: {segment}")
        ident, label, desc = match.groups()
        factors.append({"factor_id": ident, "factor_label": label,
                        "definition_text": desc, "canonical_definition": segment})
    require([r["factor_id"] for r in factors] == CATEGORY_IDS, "category order/count mismatch")
    criteria = []
    for i, line in enumerate(context["investigation_boundary"]["include"], 1):
        match = re.fullmatch(r"(R\d+(?:-[AB])?)：(.+)", line)
        if match:
            criteria.append({"criterion_id": match[1], "definition_text": match[2],
                             "canonical_definition": line, "include_index": i})
    require([r["criterion_id"] for r in criteria] == INCLUDE_IDS, "criterion definition order/count mismatch")
    return {"origin": "frozen_context_assumption", "canonical_assumption": raw,
            "factor_count": len(factors), "factor_definitions": factors}, criteria


def classify(label, criteria, require):
    flags = {r["criterion_id"]: r["status"] == "confirmed" for r in criteria}
    common = all(flags[k] for k in ("R1", "R2", "R3"))
    a = flags["R4-A"] and flags["R5-A"]
    b = flags["R4-B"] and flags["R5-B"]
    if common:
        expected = "統合型" if a and b else "品質保証型" if a else "状態基準保全型" if b else "品質推定事例"
        require(label == expected, "eligibility contradicts explicit criteria")
    else:
        require(label in {"近接事例", "除外事例"}, "eligibility contradicts common criteria")
    # Near versus excluded depends on semantic relevance, not just flags.
    return ELIGIBILITY[label]


def parse_cases(text, framework, kus, evidence, sources, *, require, lineage):
    lines = text.splitlines()
    starts = [i for i, line in enumerate(lines) if line.startswith("### C")]
    require(bool(starts), "no case sections")
    expected = [(x["factor_id"], x["factor_label"]) for x in framework["factor_definitions"]]
    cases = []
    for n, pos in enumerate(starts):
        stop = next((i for i in range(pos + 1, len(lines))
                     if lines[i].startswith(("## ", "### "))), len(lines))
        if n + 1 < len(starts):
            require(stop == starts[n + 1], "unexpected chapter between case sections")
        h = HEADER.fullmatch(lines[pos])
        require(h is not None, f"malformed case header at {pos+1}")
        cid, name = h.groups()
        body = [(i+1, lines[i]) for i in range(pos+1, stop) if lines[i].strip()]
        require(len(body) == 3 + len(expected), f"{cid}: invalid row count")
        scope = SCOPE.fullmatch(body[0][1])
        require(scope is not None, f"{cid}: malformed scope")
        full_label, raw_refs = scope.groups()
        lm = re.fullmatch(r"([^（）]+)(?:（([^（）]+)）)?", full_label)
        require(lm is not None and lm[1] in ELIGIBILITY, f"{cid}: unknown eligibility")
        label = lm[1]
        scope_refs = parse_refs(raw_refs, require)
        links = lineage(scope_refs, kus, evidence, sources)
        criteria = []
        require(body[1][1].startswith("- "), f"{cid}: malformed criteria line")
        for segment in body[1][1][2:].split(" / "):
            m = re.fullmatch(r"(R\d+(?:-[AB])?) (確認済|未確認|不適合)", segment)
            require(m is not None, f"{cid}: malformed criterion")
            ident, status = m.groups()
            criteria.append({"criterion_id": ident, "status": STATUS[status], "canonical_status": status,
                             "assessment_text": None, "reference_role": "case_scope",
                             "canonical_line": body[1][1], "analysis_line": body[1][0], **links})
        require([r["criterion_id"] for r in criteria] == CRITERION_IDS, f"{cid}: criterion order/count mismatch")
        eligibility = classify(label, criteria, require)
        reason = body[2][1]
        require(reason.startswith(REASON) and len(reason) > len(REASON), f"{cid}: missing reason")
        factors = []
        for line_no, raw in body[3:]:
            m = AXIS.fullmatch(raw)
            require(m is not None, f"{cid}: malformed category row {line_no}")
            ident, flabel, assessment, refs = m.groups()
            row_links = lineage(parse_refs(refs, require), kus, evidence, sources)
            require(set(row_links["knowledge_unit_refs"]) <= set(scope_refs), f"{cid}/{ident}: out-of-scope K")
            factors.append({"factor_id": ident, "factor_label": flabel, "canonical_status": None,
                            "applicability": None, "epistemic_status": None, "value": None,
                            "assessment_text": assessment, "limitations": None,
                            "reference_role": "category_scope", "canonical_line": raw,
                            "analysis_line": line_no, **row_links})
        require([(r["factor_id"], r["factor_label"]) for r in factors] == expected,
                f"{cid}: missing, duplicate, renamed or reordered category")
        cases.append({"case_id": cid, "name": name, "eligibility": eligibility,
                      "canonical_eligibility": label, "eligibility_detail": lm[2],
                      "assessment_reason": reason[len(REASON):],
                      "canonical_reason_line": reason, "reason_analysis_line": body[2][0],
                      "canonical_header": lines[pos], "canonical_scope_line": body[0][1],
                      "scope_analysis_line": body[0][0], "analysis_line": pos+1,
                      "knowledge_unit_scope": scope_refs, "evidence_refs": links["evidence_refs"],
                      "source_refs": links["source_refs"], "criteria_assessments": criteria,
                      "factor_assessments": factors})
    require(len({c["case_id"] for c in cases}) == len(cases), "duplicate case ID")
    headers = [line for line in lines[:starts[0]] if line.startswith("| Case |")]
    require(len(headers) == 1, "missing/duplicate summary table")
    require([s.strip() for s in headers[0].split("|")[1:-1]] ==
            ["Case", *CRITERION_IDS, "採択区分"], "summary table header mismatch")
    actual = []
    for raw in lines[:starts[0]]:
        if re.match(r"^\| C\d{2,} ", raw):
            require(raw.endswith("|"), "invalid table row")
            cells = [s.strip() for s in raw.split("|")[1:-1]]
            require(len(cells) == 9, "summary table width mismatch")
            actual.append(cells)
    wanted = [[c["case_id"], *[r["canonical_status"] for r in c["criteria_assessments"]],
               c["canonical_eligibility"] + ("（" + c["eligibility_detail"] + "）" if c["eligibility_detail"] else "")]
              for c in cases]
    require(actual == wanted, "case summary contradicts case details")
    return cases


def build_grinding_contract(context, analysis, provenance, kus, evidence, sources, *, require, lineage):
    framework, criteria = definitions(context, require)
    cases = parse_cases(analysis["working_answer"]["text"], framework, kus, evidence, sources,
                        require=require, lineage=lineage)
    factors = [r for c in cases for r in c["factor_assessments"]]
    statuses = [r["status"] for c in cases for r in c["criteria_assessments"]]
    return {"schema_version": "3.0.0", "artifact_type": "case_assessments", "authority": "derived",
            "contract": "grinding_quality_cbm_categories_v3",
            "investigation_id": context["investigation_id"], "rq_id": context["rq_id"],
            "derived_from": provenance, "factor_framework": framework,
            "criteria_definitions": criteria,
            "summary": {"case_count": len(cases), "factor_assessment_count": len(factors),
                        "criterion_assessment_count": len(statuses),
                        "eligibility_counts": dict(sorted(Counter(c["eligibility"] for c in cases).items())),
                        "factor_rows_without_explicit_status": len(factors),
                        "criterion_status_counts": dict(sorted(Counter(statuses).items()))},
            "cases": cases}
