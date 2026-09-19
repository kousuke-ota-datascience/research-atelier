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

`test_validation_contract.py` は以下を固定する。

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
