# Validation test suite

このdirectoryは、Research Atelierのdeterministic contractに対するregression testを置く。

semantic qualityやresearch conclusionの妥当性はtest対象にしない。

## 実行

repository rootで次を実行する。

```bash
python -m unittest discover -s tests -p 'test_*.py' -v
```

test file自身が `src/` をPython pathへ追加するため、editable installは不要である。

runtime dependencyとして `jsonschema` が必要。

## Test scope

`test_validation_contract.py` はlegacy v1互換性を、`test_validation_contract_v2.py` はv2 canonical identityを固定する。

- valid 00 -> 10 -> 20 -> 30 chainがPASS
- missing required fieldがFAIL
- wrong enumがFAIL
- malformed IDがFAIL
- dangling Evidence referenceがFAIL
- duplicate IDがFAIL
- Investigation ID mismatchがFAIL
- `--through 00 / 10 / 20 / 30` 相当のpartial validationが各段階でPASS

cross-artifact testは、`fixtures/v1/*.valid.min.json` を一時directoryへcanonical filenameで組み立て、各testで1条件だけ変更する。

これによりvalid fixtureを最小の利用例として保ちつつ、failure modeをtest code上で明示する。


## v2 identity regression

v2 testは以下を追加で確認する。

- `INV-NNNNNN` chainがPASSする
- Investigation IDとRQ IDにprefix dependencyがない
- artifact間の `rq_id` mismatchがFAILする
- `INV-000000` がinvalid
- staged validationがv2でもPASSする


## Working Answer body projection regression

`test_working_answer_projection.py` はBKL-0025のbody projection contractを固定する。

- accepted `30_analysis` からstructured `# Working Answer` をdeterministically render
- optional / empty chapter omission
- J/K internal lineage IDをhuman-facing viewへ露出しない
- section create / replace / NOOP
- Working Answer以外のchapter保持
- duplicate top-level headingをBLOCKED
- fenced code内の擬似headingを無視
- MISSING / STALE / CURRENT / BLOCKED state derivation
- body targetを表現するv2 projection log schema
- SUCCESS / FAILURE provenance
- Notion round-tripで除去されるordinary blank lineへ依存しないserialization


## Semantic Review persistence / reconciliation regression

`test_review_contract.py` はBKL-0027のReview persistence contractを固定する。

- append-only Review historyとper-Investigation Review Seq
- target commit / blob freezeとprepare後target変更fail-stop
- save-time Review schema validation
- Finding local IDとVerdict aggregation
- malformed / incomplete Review history検出
- `未 -> レビュー待 -> 完了 / 要修正 -> 再作業中 -> 再レビュー待` のdeterministic reconciliation
- repair開始にはexplicit eventが必要
- stale Review、duplicate / malformed history、idempotent reconciliation


## Review DB projection regression

`test_review_projection.py` はBKL-0032のGit Review JSON -> Notion Reviews operational projection contractを固定する。

- INV-000015 / Review Seq 1をregression fixtureとして 00=OK / 10=OK / 20=OK / 30=NG / Minor をderive
- Review pageのSummary / Next Action / Details / Provenance rendering
- same-Investigation 30_analysis repair handoff
- new-Investigation handoff
- frozen 00_contextへのunsafe same-Investigation repairをfail-stop
- Investigation bindingのexactly-one enforcement
- logical Review identity重複時のfail-stop
- existing row解決とLatest Review relation reconciliationのidempotence


## Split Review persistence regression

BKL-0034ではReview Cycle persistenceをcycle manifest + 4 layer JSONへ分割した。

追加で確認するcontract:

- new Review Cycleはmanifest + `review_00 / 10 / 20 / 30` の5 fileで保存される
- layer verdict / cycle verdict / Finding IDがdeterministic
- legacy single-file seqとsplit seqを同一contiguous historyとして読める
- orphan / incomplete / malformed split cycleはfail-stopする
- split cycleのdirect layer verdictとcross-layer `affected_layer` からReviews DB OK/NGをderiveする
- legacy INV-000015 Review 000001 projectionを回帰させない
