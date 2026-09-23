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
- freeze前のInvestigations DB Context inputとReview current operational state
- その他mutable operational workflow state

### Gitが正本

特定Investigationについて:

- frozen `00_context`
- frozen `10_evidence` snapshot
- `20_synthesis`
- `30_analysis`
- そのInvestigationでacceptedされたWorking Answer
- Workflow 20を実行した場合のappend-only Review JSON history / Findings / Verdict / frozen target

### Projectionは第二の正本ではない

boundaryを跨いでcopyされた値は、次のどちらかである。

- Notionからfrozen Git artifactへの **snapshot**
- GitからNotion display / operational viewへの **projection**

copyしたことで独立編集可能な第二authorityを作ってはならない。

## 2. Notion -> Git: Research Question + Investigation row -> Investigation Context freeze

`00_context`（Investigation Context）作成時は、**Research Questionのsemantic identity / wording** と **Notion Investigations DBのInvestigation-specific execution condition** を分けてreadし、1つのfrozen snapshotへmaterializeする。

### Research Questions DBからsnapshotするもの

| Notion property / value | Git 00_context field | Rule |
| --- | --- | --- |
| `RQ ID` | `rq_id` | 必須identity |
| page URL | `question.notion_url` | provenance |
| `Question` | `question.text` | frozen wording snapshot |
| `Significance` | `significance` | optional RQ-level snapshot。null可 |

原則として以下はResearch Questions DBから `00_context` へfreezeしない。

- `Status`: RQ operational state
- `Working Answer`: legacy / compatibility property。current Git-derived projection targetはRQ page bodyの `# Working Answer` section
- `Topic`: catalog organization relation
- `Parent Question`: catalog relation
- `RQ UID`: Notion内部実装用identifier。canonical snapshotには `RQ ID` とpage URLを使う

Research Questions DBには `Question Type` / `Scope` を持たない。これらはInvestigation Context属性であり、Notion Investigations DBからfreezeする。RQ側へ同名propertyを再追加して第二authorityを作らない。

### Investigations DBからsnapshotするもの

| Notion Investigations property | Git 00_context field | Rule |
| --- | --- | --- |
| `Investigation ID` | `investigation_id` | 必須identity。v2は `INV-NNNNNN` |
| `Research Question` relation | `rq_id` / `question.notion_url` のbinding validation | exactly one RQ。ID文字列からRQを推定しない |
| `Question Type` | `question_type` | null可 |
| `Scope` | `scope` | null可 |
| `Include` | `investigation_boundary.include` | 1条件1行をarrayへmaterialize |
| `Exclude` | `investigation_boundary.exclude` | 1条件1行をarrayへmaterialize |
| `Evidence Cutoff` | `investigation_boundary.evidence_cutoff` | optional |
| `Assumptions` | `assumptions` | 1 assumption 1行をarrayへmaterialize |

`Review Status` / `Latest Review Seq` はReview current operational stateであり、`00_context` へfreezeしない。

Question wordingをInvestigations DBへduplicateしない。Investigation rowの `Research Question` relation先からcurrent Questionをreadし、freeze時点のsnapshotを `question.text` とする。

### Draft / frozen authority transition

- **freeze前**: Notion Investigations rowがQuestion Type / Scope / boundary / cutoff / assumptionsのmutable operational authorityである。RQ Question / SignificanceはResearch Questions DBがcurrent authority。
- draft `00_context` を一時materializeしても、freeze完了前はcandidate representationであり、Notionと独立したcanonical authorityにはしない。
- **freeze完了後**: validation済みでcommitされたGit `00_context.json` がそのInvestigation Contextのcanonical authorityとなる。
- frozen InvestigationのNotion rowはoperational / derived viewとして残し、semantic fieldを独立編集してhistorical Git artifactを変更しない。不一致はGitを基準にreconcileする。
- freeze後にcontext-defining semantic changeが必要なら、versioning contractに従ってnew Investigationを作る。

### Existing Investigation backfill

Notion Investigations rowが存在しないhistorical Investigationをoperational registryへ登録する場合:

1. Git `00_context` をsource of truthとする。
2. `investigation_id` をrow titleへそのまま使う。legacy `RQ-NNNN-vVVV` もrenameしない。
3. `question.notion_url` / `rq_id` を使ってResearch Question relationを解決する。
4. Question Type / Scope / Include / Exclude / Evidence Cutoff / Assumptionsはfrozen `00_context` からmaterializeする。
5. current Research Questions DBのScope / Question Type等からhistorical conditionを推測補完しない。
6. backfillはRQ catalogをGitからreverse overwriteする操作ではない。

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
- Investigations.`Research Question`
- Sources.`Research Questions`
- Evidence Notes.`Source`

Gitは関連Notion pageへのimmutable provenance referenceを持ってよいが、第二のmutable relation graphは持たない。

Notion側relation変更でhistorical Investigation artifactを書き換えない。

## 5. Git -> Notion projection

### Research Question body / `# Working Answer`

決定: **accepted `30_analysis` からResearch Question page body内のtop-level `# Working Answer` sectionへprojectionする。**

authorityはaccepted Git `30_analysis` に残る。RQ page bodyの `# Working Answer` はderived operational current viewであり、第二のcanonical sourceではない。

projection authorityはWorkflow 00のfinalizationにある。**through-30 validation済みでacceptedされたInvestigationの `30_analysis` だけがprojection sourceになれる。** chat上のad hoc Web回答やcanonical artifact chainを経ていない文章を `# Working Answer` へcanonical projectionしてはならない。

body内 `# Working Answer` のhuman editはnon-canonicalであり、次回projectionで上書きされうる。canonical answerを変える場合はInvestigation lifecycle ruleに従い、Notion bodyだけを独立変更しない。

### Structured rendering contract

accepted `30_analysis` を次の順序でdeterministically renderする。

```markdown
# Working Answer
## Answer
<30_analysis.working_answer.text>
## Key Judgments
- <30_analysis.judgments[].statement>
## Limitations
- <30_analysis.limitations[].text>
## Unresolved Questions
- <30_analysis.unresolved_questions[]>
## Alternative Interpretations
- <30_analysis.alternative_interpretations[].text>
```

rule:

- `# Working Answer` と `## Answer` は常に生成する。
- `Key Judgments` / `Limitations` / `Unresolved Questions` / `Alternative Interpretations` は、対応arrayが空またはfieldが存在しない場合、そのchapter自体を省略する。空chapterを生成しない。
- `J####` / `K####` 等の内部lineage IDは通常のhuman-facing current viewへ露出させない。canonical lineageはGit artifact内に保持する。
- body表示用の新しい要約・再解釈を生成しない。accepted `30_analysis` のtext fieldをそのままrenderする。
- Notionは通常の空行をwrite/read round-tripで保持しないため、canonical serializationは空行separatorを持たないblock sequenceとする。視覚的spacingはNotion block layoutへ委譲する。

### Safe body update semantics

projection adapterはRQ page body全体を意味的に再構築しない。`src/research_atelier/projection/working_answer.py` のdeterministic renderer / section patch contractに従う。

- top-level exact heading `# Working Answer` をtargetとし、次のtop-level H1直前までをsection boundaryとする。
- targetが0件ならRQ body末尾へ新規作成する。
- targetが1件なら、そのsectionだけをcurrent accepted renderingへreplaceする。
- current renderingと一致する場合はNOOPとし、timestamp更新だけを理由にNotion bodyを書き換えない。
- target headingが2件以上存在する場合、どれを上書きするか推測せずprojectionを **BLOCKED** とする。重複headingを人間または明示的repairで解消してから再実行する。
- fenced code block内の `# Working Answer` はsection headingとして数えない。
- projection後はRQ pageを再取得し、unique `# Working Answer` sectionがdeterministic renderingと一致することを確認する。
- Working Answer以外のchapter、手書き本文、関連メモは保持する。

### Legacy `Working Answer` property

既存の `Research Questions.Working Answer` propertyは削除しない。**legacy / compatibility fieldとして残すが、新contractではcanonical projection targetではない。**

- migration時にexisting valueを削除しない。
- body projection成功後にpropertyへdual-writeしない。
- propertyがempty / legacy / staleでもWorkflow 00のCOMPLETE判定を妨げない。
- propertyとbodyが異なる場合、accepted Git `30_analysis` とbody内 `# Working Answer` をcurrent projectionとして扱う。
- property valueからbodyやGit `30_analysis` をreverse reconstructionしない。
- 将来property自体をdeprecated表示または削除する場合は、別ticketでschema / migrationを明示的に扱う。

### v2でprojectionしないもの

Gitから通常のfinalization write-backとして自動projectionしない:

- `20_synthesis`
- Evidence snapshot content
- Question Type / Scope / Significance
- Source / Evidence Note record
- Topic / Source relation

ただし、**Investigations DB rowのcontrolled backfill / frozen-context reconciliationは例外**であり、既存Git `00_context` がauthorityのとき、そのContext fieldをNotion operational rowへmaterializeしてよい。この操作はResearch Question catalogへのreverse reconstructionではない。

`judgments` / `limitations` / `unresolved_questions` / `alternative_interpretations` は独立したNotion propertyへprojectionせず、上記structured `# Working Answer` current view内だけにrenderする。

### Research Question Status

`Status` はNotion-authoritative operational stateとする。

Working Answer body projection成功だけで `Status = Answered` へ自動変更しない。

自動更新するなら、別仕様とtestを定義してから導入する。

## 6. Projection provenance

projection provenance専用のNotion propertyは追加しない。

new body projectionは、historical `projection_log.json` をrewriteせず、Investigation directoryの `projection_log_v2.json` に記録する。schemaは `schemas/v2/projection_log.schema.json` を正本とする。

少なくとも以下をlogする。

- target RQ page URL
- `rq_id`
- source `investigation_id`
- accepted `30_analysis` を含むGit commit SHA
- projection timestamp
- `projection_target.surface = page_body`
- `projection_target.section_heading = "# Working Answer"`
- success / failure
- failure時は可能な範囲で原因を `note` に記録する

BKL-0025以前のproperty projectionを記録したhistorical `projection_log.json` はその時点の事実として保持し、`target_property` をbody targetへ書き換えない。

Notion property数を増やさずauditabilityを確保する。

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

Notion current stateからretryするか、Investigation Contextをfreeze後に変更する必要があるなら新しいInvestigationを作る。

### Git -> Notion projection failure

Gitが正本のままである。

RQ page bodyの `# Working Answer` sectionはstale / missingになりうる。

stale / missing body projectionやlegacy `Working Answer` propertyへ合わせてGitを書き換えてはならない。

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
- update後Evidenceを使う新analysisは未accept Investigationを更新するか、新しいInvestigationを作る
- accepted Investigationへ実質的に異なるEvidenceを組み込む場合は新しいInvestigation

## 10. Reliability Note boundary

`Sources.Reliability Note` は自動的にEvidence contentへfreezeしない。

これはmutable catalog-level assessmentであり、analyst judgmentを含みうる。

reliability concernがInvestigation conclusionへ重要なら、traceable supportとともに `20_synthesis` uncertaintyまたは `30_analysis` limitation / judgmentとして明示する。

mutable Reliability NoteをEvidence layerへ暗黙copyしない。

## 11. No reverse reconstruction rule

Git artifactからNotion catalog全体を再構築・overwriteしてはならない。また、Notion body / legacy propertyからGit canonical analysisをreverse reconstructionしてはならない。

禁止例:

- `10_evidence` からSourcesを生成しGitをSource authority扱いする
- `20_synthesis` からEvidence Notesを生成する
- historical `00_context` からRQ Questionをoverwriteする
- historical `00_context` のScope / Question TypeをResearch Questions DBへ逆投影し、RQ-level propertyを再作成する
- frozen Git referenceからResearch Topics / Research Questions / Sources / Evidence Notes等のcatalog relationを再構築する
- ただしBKL-0028で定義したInvestigations DB rowのbackfill / frozen-context reconciliationは、`00_context` のexplicit RQ provenanceを用いる限定的な例外とする
- body内 `# Working Answer` のhuman editから `30_analysis` を更新する
- legacy `Research Questions.Working Answer` propertyからbodyまたは `30_analysis` を再構築する

projectionは意図的に狭く保つ。

## 12. Operational contract

v2におけるResearch QuestionへのGit write-backは次のderived body projectionだけとする。

```text
accepted 30_analysis
    -> Research Question page body
       -> # Working Answer
          -> deterministic structured current view
```

legacy `Research Questions.Working Answer` propertyへはwrite-backしない。

その他は:

- Notion -> Git freeze
- Git-only canonical research artifact
- Notion-only reusable catalog / operational state

このboundaryでdual authorityを防ぐ。


## 13. Investigation identity migration

新規freezeではv2 canonical ID `INV-NNNNNN` を使用し、`rq_id` は独立fieldとしてsnapshotする。

既存 `RQ-NNNN-vVVV` artifactはlegacy v1として保持し、projection provenanceでもhistorical `investigation_id` をそのまま記録する。過去artifactをv2 IDへrenameしない。


## 14. Working Answer body migration

property projection済みRQを新contractへ移行する場合:

1. accepted Git `30_analysis` とそのcommit SHAをsourceとして確定する。
2. existing RQ bodyを取得し、safe body update semanticsを適用する。
3. legacy `Working Answer` propertyからcontentをreverse reconstructionしない。
4. body内 `# Working Answer` をcreate / replaceし、再取得してcurrent renderingと一致することを確認する。
5. legacy propertyは削除・clear・dual-writeしない。
6. historical `projection_log.json` はrewriteせず、新body projectionを `projection_log_v2.json` として記録する。

## 15. Deterministic implementation boundary

Working Answer body rendering / section patch / projection-current判定 / v2 log materializationのcanonical helper implementationは `src/research_atelier/projection/working_answer.py` とする。

Notion APIの認証・fetch・update自体はWorkflow 00のprojection adapter責務である。adapterはhelperのresultを尊重し、独自のsection parsing / rendering ruleを再実装しない。

projection adapterがNotion writeに失敗した場合はGit artifactを変更せず、failure provenanceを残してstateをCOMPLETEへ進めない。

## 16. Git Review -> Notion Investigation Review current state

Workflow 20を実行した場合、canonical Review contentはGitに保持し、NotionにはBKL-0032で定義したderived operational projectionをreconcileする。

```text
Git canonical Review JSON history
    |
    | deterministic projection / reconcile
    v
Reviews DB (human-facing derived view)
    |
    | latest relation
    v
Investigations DB
    ├─ Review Status
    ├─ Latest Review
    └─ Latest Review Seq (compatibility)
```

### Authority

Git authority:

- Review Seq history
- target commit SHA / artifact blob SHA
- transition別semantic assessment
- Findings
- severity / evidence / impact / repair direction
- cycle Verdict

Notion authorityではなくderived operational surface:

- Investigations DB: `Review Status` / `Latest Review` / `Latest Review Seq`
- Reviews DB: `Verdict` / artifact-level OK・NG / Highest Severity / Finding details / provenance

Reviews DBへのFinding本文・Verdict・target provenanceの表示は、Git canonical Review JSONからのdeterministic projectionとしてのみ許可する。Notion上の値をReview semantic authorityとして扱わず、Gitへreverse applyしない。pre/post SHA等の独立control-plane propertyは追加しない。

### Status contract

許容値は以下の7値に限定する。

- `未`
- `レビュー待`
- `要修正`
- `再作業中`
- `再レビュー待`
- `完了`
- `－（対象外）`

`未` はoptional Review process未開始、`－（対象外）` は明示的な対象外decisionである。Git factsだけから `－（対象外）` を推測しない。

`要再調査` / `レビュー中` はpersistent Statusとして追加しない。new Investigation handoffはFindingの `repair_direction.mode = new_investigation` とversioning contractで表す。

### Reconciliation

state transition / fail-stop / mutation planは `src/research_atelier/reviewing/reconcile.py` をcanonical deterministic implementationとする。

- Workflow 20はReview JSON保存後にNotion Statusを直接writeしない。
- Workflow 00 / connector adapterはGit Review facts、current target relation、explicit eventsをreconcilerへ入力する。
- `repair_started` は実際にsame-Investigation repair phaseへ入った時だけWorkflow 00が発行する。
- malformed / duplicate / incomplete Review history、target ahead / divergedはBLOCKEDとし、mutationを適用しない。
- stale Reviewはcurrent targetのPass証明ではなく、reReview対象として扱う。
- mutation適用後はReviews rowとInvestigation rowを再取得し、Review projectionおよび `Review Status / Latest Review / Latest Review Seq` がplanと一致することをverifyする。

このprojectionはReview semantic authorityのtransferではない。Notion rowはcurrent pointerであり、Git Review JSONがcanonical Review factのままである。



## 17. Reviews DB projection contract / BKL-0032

BKL-0032は、BKL-0027でdeferしていたReview DBを**human-facing operational projection**として採用する変更である。これはReviewをcore first-class domain entityへ昇格させる変更ではない。

### Identity / authority

- logical Review identity: `(Investigation ID, Review Seq)`
- canonical authority: Git `investigations/<INV>/reviews/review-XXXXXX.json`
- Notion Reviews row: canonical JSONから再構築可能なderived view
- global `REV-NNNN`: 導入しない

### Projection mapping

| Git Review fact | Notion Reviews |
| --- | --- |
| `investigation_id` | `Investigation` relation + title |
| `review_seq` | `Review Seq` |
| deterministic `verdict` | `Verdict` |
| Finding / transition | `00 Context / 10 Evidence / 20 Synthesis / 30 Analysis` OK/NG |
| Finding severity | `Highest Severity` |
| `reviewed_at` | `Reviewed At` |
| assessment / Finding / repair direction / target provenance | Review page body |

artifact-level OK/NGはmanual fieldではない。transition Findingと `repair_direction.affected_layer` からderiveする。

### Human-facing body

Review page bodyは `Summary -> Next Action — Quick Reference -> Review Details -> Provenance` の順でrenderする。

Next Actionはcanonical Findingから導出する。

- `new_investigation` が必要ならWorkflow 00へhandoffする。
- same-Investigation repairは最上流のaffected layerからWorkflow 10をresumeし、現行 `10 -> 20 -> 30` invalidation ruleに従う。
- frozen `00_context` のsame-Investigation repairはunsafeとしてfail-stopする。

### Idempotence / failure

canonical implementationは `src/research_atelier/projection/review.py`。

- Investigation bindingはexactly one row必須。
- logical Review identityはNotionで0または1 rowのみ許容する。
- duplicate rowは自動mergeせずBLOCKED。
- latest canonical Reviewに対応するrowが成立しない状態で `Latest Review` relationだけ更新しない。
- 同一Git factsから再実行した場合、Review row追加や不要なpointer mutationを行わない。
- Notion write失敗・projection driftはGit Review JSONを変更する根拠にしない。

`Latest Review Seq` はmigration compatibilityのため当面保持する。human navigationには `Latest Review` relationを使う。
