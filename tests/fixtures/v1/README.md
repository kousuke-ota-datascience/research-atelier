# v1 fixture

このdirectoryはResearch Schema v1の最小exampleを保持する。

## Naming rule

- `*.valid.min.json`: 対応SchemaをPASSする最小例
- `*.invalid.<reason>.json`: file名で示した構造違反によりFAILする例

## Valid chain

以下4 fileは同じ `RQ-0007-v001` を使用し、test suiteで1本のcanonical chainとして組み立てられる。

1. `00_context.valid.min.json`
2. `10_evidence.valid.min.json`
3. `20_synthesis.valid.min.json`
4. `30_analysis.valid.min.json`

`00_context` はdraftかつQuestion Type unknownの最小例であるため、`30_analysis` のCausal profileと矛盾しない。reference validatorはfrozen contextに明示されたQuestion Typeがある場合だけAnalysisとの一致を強制する。

## Invalid examples

- `00_context.invalid.identity.json`: malformed identityと許可されないfield
- `10_evidence.invalid.analysis-field.json`: Evidence layerへのanalysis judgment混入
- `20_synthesis.invalid.working-answer.json`: Synthesis layerへのWorking Answer混入
- `30_analysis.invalid.evidence-bypass.json`: Analysisからraw Evidenceを直接参照
- `30_analysis.invalid.profile-mismatch.json`: Causal profileへPredictive専用fieldを混入

missing required / wrong enum / duplicate ID / dangling reference / Investigation mismatchは、valid fixtureをtest内で1点だけmutationして検査する。これにより同じfailureを表すfixtureを大量に複製しない。
