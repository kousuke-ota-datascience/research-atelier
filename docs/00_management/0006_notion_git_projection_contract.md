# Notion <-> Git Projection Contract

## 目的

本書は、NotionのResearch DBとGit上のcanonical Investigation artifactの間にある、方向付きdata contractを定義する。

対称なtwo-way syncは行わない。

```text
Notion reusable catalog / operational state
        |
        | selected stateをfreeze
        v
Git canonical Investigation artifacts
        |
        | accepted outputの一部をprojection
        v
Notion operational current state
```

authorityは常に `0001_research_architecture.md` に従う。

## 1. Authority summary

### Notionが正本

- Research Topics catalog / topic relation
- current Research Question catalog state
- Source bibliographic identity / metadata
- reusable Evidence Notes
- mutable operational workflow state

### Gitが正本

特定Investigation versionについて:

- frozen `00_context`
- frozen `10_evidence` snapshot
- `20_synthesis`
- `30_analysis`
- そのversionでacceptedされたWorking Answer

### Projectionは第二の正本ではない

boundaryを跨いでcopyされた値は、次のどちらかである。

- Notionからfrozen Git artifactへの **snapshot**
- GitからNotion display / operational propertyへの **projection**

copyしたことで独立編集可能な第二authorityを作ってはならない。

## 2. Notion -> Git: Research Question freeze

`00_context` 作成時、Research Questions DBの以下をfreezeする。

| Notion property | Git 00_context field | Rule |
| --- | --- | --- |
| `RQ ID` | `rq_id` | 必須identity |
| page URL | `question.notion_url` | provenance |
| `Question` | `question.text` | frozen wording snapshot |
| `Question Type` | `question_type` | draftではnull可 |
| `Scope` | `scope` | null可 |
| `Significance` | `significance` | null可 |

原則として以下は `00_context` へfreezeしない。

- `Status`: Notion operational state
- `Working Answer`: Git-derived projection target
- `Topic`: catalog organization relation
- `Parent Question`: catalog relation
- `RQ UID`: Notion内部実装用identifier。canonical snapshotには `RQ ID` とpage URLを使う

Investigation-specific boundary / assumptionsはGitの `00_context` で管理し、RQ recordへduplicate propertyとして書き戻さない。

## 3. Notion -> Git: Evidence freeze

### Source / Evidence Noteの役割

`Sources` と `Evidence Notes` はreusable Notion catalogである。

`10_evidence` はDB mirrorではない。そのInvestigationで選択したEvidenceのsnapshotである。

### Evidence Note mapping

| Notion Evidence Notes property | Git 10_evidence field | Rule |
| --- | --- | --- |
| page URL | `provenance.evidence_note.notion_url` | stable provenance |
| `Evidence Note` | `content` + optional title | source-faithful text |
| `Note Type` | `note_type` | classificationを保持 |
| `Location` | `source_locator` | source locationを保持 |
| `Direct Quote` | `direct_quote` | 存在する場合exact quoteを保持 |
| `Source` relation target URL | `provenance.source.notion_url` | Source lineage |

`10_evidence.evidence_id` はInvestigation-localなlineage IDであり、`20_synthesis.evidence_refs` から参照される。Notionのformula `Evidence ID` を複製管理するものではない。

### Source mapping

Gitには、Notion Sourceを特定するために必要な最小provenanceのみを保存する。

- Source page URL
- 可読性のためのoptional Source title

以下はNotion-authoritativeのままとし、`10_evidence` へ一式copyしない。

- `Source ID`
- `Source Type`
- `Journal / Publisher`
- `Authors`
- `Year`
- `URL`
- `DOI`
- `PDF / File`
- `Reading Status`
- `Reliability Note`
- `Research Questions` relation

Investigationがfreezeするのは「実際に使用したEvidence」であり、第二のbibliographic DBではない。

将来、厳密なhistorical bibliography snapshotが再現性上必要になった場合は、mutable Source fieldsをad hocに複製せず、citation snapshot contractを別途定義する。

## 4. writable relationを二重管理しない

以下のrelationはNotionのみを正本とする。

- Research Topics.`Parent Topic`
- Research Topics.`Research Questions`
- Research Questions.`Topic`
- Research Questions.`Parent Question`
- Sources.`Research Questions`
- Evidence Notes.`Source`

Gitは関連Notion pageへのimmutable provenance referenceを持ってよいが、第二のmutable relation graphは持たない。

Notion側relation変更でhistorical Investigation artifactを書き換えない。

## 5. Git -> Notion projection

### RQ.Working Answer

決定: **Gitからprojectionする。**

Notion Research Questionsの `Working Answer` は、そのRQについてlatest accepted `30_analysis.working_answer.text` を示すderived operational viewとする。

authorityはaccepted Git `30_analysis` に残る。

したがって:

- Notion `Working Answer` のhuman editはnon-canonical
- 次回projectionで上書きされうる
- canonical answerを変える場合はversioning ruleに従ってInvestigation Analysisを変更し、Notionだけを独立変更しない

### v1でprojectionしないもの

Gitから自動projectionしない:

- `20_synthesis`
- individual judgment
- limitation
- unresolved question
- Evidence snapshot content
- Question Type / Scope / Significance
- Source / Evidence Note record
- Topic / Source relation

必要なら将来derived viewとして追加する。

### Research Question Status

`Status` はNotion-authoritative operational stateとする。

Working Answer projection成功だけで `Status = Answered` へ自動変更しない。

自動更新するなら、別仕様とtestを定義してから導入する。

## 6. Projection provenance

v1ではprojection provenance専用のNotion propertyを追加しない。

projection operationは少なくとも以下をlogする。

- target RQ page URL
- `rq_id`
- source `investigation_id`
- accepted `30_analysis` を含むGit commit SHA
- projection timestamp
- success / failure

Notion property数を増やさずauditabilityを確保する。

pilotでNotion上からsource Investigationを直接確認する必要性が明確になった場合、複数fieldを埋め込むのではなく専用provenance property 1つを追加する。

## 7. Freeze transaction rule

Notion -> Git freezeは、以下すべてを満たしたときだけ成功とみなす。

1. source Notion recordをreadした
2. target Git artifactをmaterializeした
3. JSON Schema validationがPASSした
4. 実装済みdeterministic identity / lineage validationがPASSした
5. 完全なtarget artifactをGit commitした

partial writeはvalid snapshotではない。

freeze失敗時、missing valueを捏造せず、previous accepted Investigationを変更しない。

## 8. Sync / projection failure

### Notion -> Git freeze failure

新snapshot成立前はNotionがcurrent catalog stateの正本である。

failed / partial Git candidateはcanonicalではない。

previous committed Investigationは、そのhistorical versionについて引き続きcanonicalである。

Notion current stateからretryするか、Research Contextが変わったなら新Investigation versionを作る。

### Git -> Notion projection failure

Gitが正本のままである。

Notion `Working Answer` はstaleになりうる。

stale Notion値へ合わせてGitを書き換えてはならない。

accepted Git artifactからprojectionをretryする。

### Current Notionとhistorical Gitの差異

current RQがNotionで変更され、older frozen Git contextと異なっていても、それ自体はsync conflictではない。

- Notion = current mutable catalog
- Git = historical frozen Investigation

新Investigationが新しいNotion stateをsnapshotする。

## 9. Source / Evidence Note update semantics

Investigationが `10_evidence` をfreezeした後にNotion Source / Evidence Noteが変更された場合:

- historical `10_evidence` は不変
- Notion catalogはcurrent reusable recordを保持
- update後Evidenceを使う新analysisは未accept Investigationを更新するか、新versionを作る
- accepted Investigationへ実質的に異なるEvidenceを組み込む場合は新Investigation version

## 10. Reliability Note boundary

`Sources.Reliability Note` は自動的にEvidence contentへfreezeしない。

これはmutable catalog-level assessmentであり、analyst judgmentを含みうる。

reliability concernがInvestigation conclusionへ重要なら、traceable supportとともに `20_synthesis` uncertaintyまたは `30_analysis` limitation / judgmentとして明示する。

mutable Reliability NoteをEvidence layerへ暗黙copyしない。

## 11. No reverse reconstruction rule

Git artifactからNotion catalog全体を再構築・overwriteしてはならない。

禁止例:

- `10_evidence` からSourcesを生成しGitをSource authority扱いする
- `20_synthesis` からEvidence Notesを生成する
- historical `00_context` からRQ Question / Scope / Question Typeをoverwriteする
- frozen Git referenceからNotion relationを再構築する

projectionは意図的に狭く保つ。

## 12. Operational contract

v1における4 Research DBへのGit write-backは次の1つだけ。

```text
accepted 30_analysis.working_answer.text
    -> Research Questions.Working Answer
```

その他は:

- Notion -> Git freeze
- Git-only canonical research artifact
- Notion-only reusable catalog / operational state

このboundaryでdual authorityを防ぐ。
