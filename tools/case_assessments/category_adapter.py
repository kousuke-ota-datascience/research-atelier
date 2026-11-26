"""製造品質分析のカテゴリ記述形式（contract v2）を原文保持で抽出する。

採択条件ごとの個別根拠、カテゴリ全体の適用可否・認識状態は
正本に明示されていないため、生成器で推定しない。
"""
from __future__ import annotations

from collections import Counter
import re

PREFIX = "事例記述軸は本調査固有の次の9カテゴリとする。"
CATEGORY_IDS = [f"D{i:02d}" for i in range(1, 10)]
CRITERION_IDS = [f"R{i}" for i in range(1, 5)]
STATUS = {"確認済": "confirmed", "未確認": "unconfirmed", "不適合": "not_met"}
ELIGIBILITY = {"完全適合": "full_match", "要因分析": "factor_analysis", "近接": "near_match", "除外": "excluded"}
HEADER = re.compile(r"^### (C\d{2,}) (.+)$")
SCOPE = re.compile(r"^- 採択区分：([^（]+)（([^）]+)）$")
AXIS = re.compile(r"^- (D\d{2}) ([^：]+)：(.+)（(K\d{4}[^（）]*)）。$")
REF = re.compile(r"K(\d{4})(?:[–-]K(\d{4}))?")


def parse_refs(raw, require):
    refs = []
    for part in re.split(r"[,、]\s*", raw):
        m = REF.fullmatch(part)
        require(m is not None, f"malformed K reference: {part}")
        lo = int(m.group(1))
        hi = int(m.group(2)) if m.group(2) else lo
        require(0 < lo <= hi, f"invalid reference range: {part}")
        refs.extend(f"K{i:04d}" for i in range(lo, hi + 1))
    require(len(refs) == len(set(refs)), "duplicate K references")
    return refs


def definitions(context, require):
    candidates = [x for x in context["assumptions"] if x.startswith(PREFIX)]
    require(len(candidates) == 1, "expected one explicit nine-category contract")
    raw = candidates[0]
    m = re.fullmatch(re.escape(PREFIX) + r"(.+?)。各カテゴリを記述し、.+", raw)
    require(m is not None, "malformed category framework")
    factors = []
    for segment in m.group(1).split("、"):
        match = re.fullmatch(r"(D\d{2}) ([^（]+)（([^）]+)）", segment)
        require(match is not None, f"invalid category definition: {segment}")
        ident, label, description = match.groups()
        factors.append({"factor_id": ident, "factor_label": label,
                        "definition_text": description, "canonical_definition": segment})
    require([x["factor_id"] for x in factors] == CATEGORY_IDS, "category definition order/count mismatch")
    criteria = []
    for index, line in enumerate(context["investigation_boundary"]["include"], 1):
        match = re.fullmatch(r"(R\d+)：(.+)", line)
        if match:
            criteria.append({"criterion_id": match.group(1), "definition_text": match.group(2),
                             "canonical_definition": line, "include_index": index})
    require([x["criterion_id"] for x in criteria] == CRITERION_IDS, "criterion definition order/count mismatch")
    return {"origin": "frozen_context_assumption", "canonical_assumption": raw,
            "factor_count": len(factors), "factor_definitions": factors}, criteria


def parse_cases(text, framework, kus, evidence, sources, *, require, lineage):
    lines = text.splitlines()
    # Explicitly bound the case chapter; non-case chapters are not case rows.
    marker = "## 事例別9カテゴリ"
    require(lines.count(marker) == 1, "missing or duplicate case chapter")
    start = lines.index(marker)
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    starts = [i for i in range(start + 1, end) if lines[i].startswith("### ")]
    require(bool(starts), "no case sections")
    require(all(not line.startswith("### C") for line in lines[:start] + lines[end:]), "case outside case chapter")
    expected = [(x["factor_id"], x["factor_label"]) for x in framework["factor_definitions"]]
    cases = []
    for n, pos in enumerate(starts):
        stop = starts[n + 1] if n + 1 < len(starts) else end
        h = HEADER.fullmatch(lines[pos])
        require(h is not None, f"malformed header at {pos+1}")
        cid, name = h.groups()
        body = [(i+1, lines[i]) for i in range(pos+1, stop) if lines[i].strip()]
        require(len(body) == 3 + len(expected), f"{cid}: invalid case row count")
        scope = SCOPE.fullmatch(body[0][1])
        require(scope is not None, f"{cid}: invalid scope row")
        label, raw_refs = scope.groups()
        require(label in ELIGIBILITY, f"{cid}: unknown eligibility")
        scope_refs = parse_refs(raw_refs, require)
        links = lineage(scope_refs, kus, evidence, sources)
        criteria = []
        for segment in body[1][1].removeprefix("- ").split(" / "):
            m = re.fullmatch(r"(R\d+) (確認済|未確認|不適合)", segment)
            require(m is not None and body[1][1].startswith("- "), f"{cid}: malformed criterion")
            ident, status = m.groups()
            criteria.append({"criterion_id": ident, "status": STATUS[status], "canonical_status": status,
                             "assessment_text": None, "reference_role": "case_scope",
                             "canonical_line": body[1][1], "analysis_line": body[1][0], **links})
        require([r["criterion_id"] for r in criteria] == CRITERION_IDS, f"{cid}: criterion order/count mismatch")
        confirmed = [r["status"] == "confirmed" for r in criteria]
        require((label == "完全適合") == all(confirmed), f"{cid}: full-match contradiction")
        require((label == "要因分析") == (all(confirmed[:3]) and not confirmed[3]), f"{cid}: factor-analysis contradiction")
        reason = body[2][1]
        require(reason.startswith("- 判定理由：") and len(reason) > len("- 判定理由："), f"{cid}: missing reason")
        factors = []
        for line_no, raw in body[3:]:
            m = AXIS.fullmatch(raw)
            require(m is not None, f"{cid}: malformed category line {line_no}")
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
        cases.append({"case_id": cid, "name": name, "eligibility": ELIGIBILITY[label],
                      "canonical_eligibility": label, "assessment_reason": reason.removeprefix("- 判定理由："),
                      "canonical_reason_line": reason, "reason_analysis_line": body[2][0],
                      "canonical_header": lines[pos], "canonical_scope_line": body[0][1],
                      "scope_analysis_line": body[0][0], "analysis_line": pos+1,
                      "knowledge_unit_scope": scope_refs, "evidence_refs": links["evidence_refs"],
                      "source_refs": links["source_refs"], "criteria_assessments": criteria,
                      "factor_assessments": factors})
    require(len({c["case_id"] for c in cases}) == len(cases), "duplicate case ID")
    # Cross-check the independently stated canonical summary table; separator
    # is formatting only, not a data row (including surplus dash cell).
    table = [line for line in lines[:start] if re.match(r"^\| C\d{2,} ", line)]
    actual = []
    for raw in table:
        require(raw.endswith("|"), "invalid summary table row")
        cells = [s.strip() for s in raw.split("|")[1:-1]]
        require(len(cells) == 6, "summary table width mismatch")
        actual.append(cells)
    wanted = [[c["case_id"] + " " + c["name"],
               *[r["canonical_status"] for r in c["criteria_assessments"]],
               c["canonical_eligibility"]] for c in cases]
    require(actual == wanted, "case summary table contradicts case details")
    return cases


def build_category_contract(context, analysis, provenance, kus, evidence, sources, *, require, lineage):
    framework, criteria = definitions(context, require)
    cases = parse_cases(analysis["working_answer"]["text"], framework, kus, evidence, sources,
                        require=require, lineage=lineage)
    factors = [r for c in cases for r in c["factor_assessments"]]
    statuses = [r["status"] for c in cases for r in c["criteria_assessments"]]
    return {"schema_version": "2.0.0", "artifact_type": "case_assessments", "authority": "derived",
            "contract": "manufacturing_quality_categories_v2",
            "investigation_id": context["investigation_id"], "rq_id": context["rq_id"],
            "derived_from": provenance, "factor_framework": framework,
            "criteria_definitions": criteria,
            "summary": {"case_count": len(cases), "factor_assessment_count": len(factors),
                        "criterion_assessment_count": len(statuses),
                        "eligibility_counts": dict(sorted(Counter(c["eligibility"] for c in cases).items())),
                        "factor_rows_without_explicit_status": len(factors),
                        "criterion_status_counts": dict(sorted(Counter(statuses).items()))},
            "cases": cases}
