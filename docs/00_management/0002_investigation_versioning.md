# Investigation identity / versioning

## 目的

本書は、長期的に維持される Research Question（RQ）と、ある具体的Research Contextをfreezeした versioned Investigation の関係を定義する。

本書は `0001_research_architecture.md` に従う。mutableなRQ catalogはNotionが正本であり、frozen Investigation versionはGit artifactが正本である。

## 1. RQとInvestigationは別identity

### Research Question (RQ)

RQは、追究する問いの長期的identityである。

RQは「何を問うか」という安定した概念的意図を持つ。Notion上のrecordは運用上更新されうるが、過去のInvestigationがその編集を暗黙に継承してはならない。

例:

`RQ-0007`

### Investigation

Investigationは、特定のfrozen Research Contextの下でRQを1回実行した単位である。

問いのsnapshotと、Evidenceを選択・Synthesis・Analysisした条件を記録する。

例:

`RQ-0007-v001`

同一RQに複数Investigationが存在しうる。

- `RQ-0007-v001`
- `RQ-0007-v002`
- `RQ-0007-v003`

各versionは独立に解釈可能であり、Notion側のRQが後から更新されてもhistorical versionの意味は変わらない。

## 2. Identifier形式

### RQ ID

canonical form:

`RQ-<NNNN>`

v1では `NNNN` は0埋め4桁の10進数とする。

Regex:

`^RQ-[0-9]{4}$`

例:

- valid: `RQ-0001`
- valid: `RQ-0427`
- invalid: `RQ-7`
- invalid: `rq-0007`

RQが9999件を超える場合は、formatを暗黙に拡張せずidentifier contractを明示的にmigrationする。

### Investigation ID

canonical form:

`<RQ_ID>-v<VVV>`

v1では `VVV` は0埋め3桁、`001` から開始し、RQごとに単調増加させる。

Regex:

`^RQ-[0-9]{4}-v[0-9]{3}$`

例:

- `RQ-0007-v001`
- `RQ-0007-v002`

一度canonical Investigationとしてcommitしたversion番号は再利用してはならない。

## 3. Lifecycle / mutation rule

Investigation versionには、versioning上2つのphaseがある。

### Draft context

Research Contextをfreezeする前は、同じInvestigation versionをin-placeで修正してよい。

同一draft versionで許容する代表例:

- RQ identityを変えないquestion wordingの改善
- 未確定だったScope / Significanceの追記
- Question Typeの訂正
- investigation boundaryの具体化
- 不足context fieldの追記
- freeze前に発見した誤りの修正

unknownは有効な状態である。未確定fieldはSchemaが許す範囲で省略または `null` とし、validationを通すための架空defaultを入れてはならない。

### Frozen context

`00_context` をEvidence収集のbaselineとして明示的に受け入れた時点をfreeze pointとする。

freeze後、context-defining fieldをin-placeで変更してはならない。

context-defining fieldを変更する場合は次のInvestigation versionを採番する。

`10_evidence`、`20_synthesis`、`30_analysis` はそのfrozen contextの下で構築する。Investigation resultをacceptするまでは同一version内で反復改善してよい。

Investigation resultをacceptした後、Evidence snapshotまたはaccepted Analysisを実質的に変更する場合も新versionを必要とする。historical accepted artifactを書き換えてはならない。

## 4. 新Investigation versionが必要な変更

基礎となるRQ identityが同一である前提で、freeze後に以下が変わる場合は新versionを作る。

- question snapshotの意味が変わる
- Scopeが変わる
- Question Typeが変わる
- investigation boundary / inclusion-exclusion criteriaが変わる
- eligible Evidenceへ影響するtime horizon / evidence cutoffが変わる
- 解釈を定義するanalytical assumptionが変わる
- accepted Investigationを実質的に異なるEvidenceで再実行する

canonical inputを変更してaccepted resultを再計算する場合も新versionとする。

## 5. 新versionを必要としない変更

以下では新Investigation versionは不要。

- contextがdraftの間の編集
- formattingのみの変更
- 意味を変えないことが明らかな誤字・文法修正
- canonical input/outputを変えないvalidator refactoring
- 不変canonical artifactからderived renderingを再生成するだけの変更
- frozen Research Contextに含まれないNotion operational metadataの変更

Git historyには実装・format変更が残るが、Investigation versioningはresearch-semantic changeに対して使う。

## 6. Question wording rule

### 非意味的変更

許容される回答集合、および意図するconstruct / estimandが変わらない場合、RQ identityは同一とする。

例:

- 文法修正
- 用語表記統一
- 意味を変えない明確化

draft Investigationなら同一versionを更新してよい。

freeze済みInvestigationはhistorical question snapshotを保存する。将来の新実行では更新後のwordingを次versionにsnapshotしてよいが、過去versionは書き換えない。

### 意味的変更

何が回答になりうるかを実質的に変える場合、それはInvestigation version変更ではなく新RQ identityである。

判断材料の例:

- target construct
- 問いに本質的なpopulation / unit of analysis
- causal treatment / comparator
- outcome
- prediction target
- central mechanism

不明な場合は既存RQを維持する側を基本とし、answer spaceが実質的に変わる場合だけ新RQを作る。関連RQはNotionでlinkしてよい。

## 7. Scope変更

Scopeは原則としてRQ identityではなくInvestigationを定義する。

- freeze前: 同一versionを更新
- freeze後: 次versionを採番

ただしScope変更が概念的な問いそのものを変える場合は新RQとする。

## 8. Question Type変更

Question Typeはdownstream Analysis Profileを選択・制約する。

したがって:

- freeze前: 同一versionを更新
- freeze後: 次versionを採番

Question Typeは分析分類であり、単独の変更では通常RQ identityを変えない。

## 9. Significanceなど未確定field

Significanceはunknownを許容する。

workflowは以下を含むInvestigation draftを扱えなければならない。

- Scope unknown
- Significance unknown
- investigation boundaryの一部がpending

unknownはJSON Schemaに従い、省略または `null` で表す。`TBD`、空文字、架空defaultをcanonical valueとして使わない。

後からNotionのSignificanceが変更されても、frozen Investigationを遡及変更しない。新しい実行を意図的に作る場合にだけ、その時点の値をsnapshotする。

## 10. Version allocation algorithm

新しいRQ実行では:

1. RQ IDを読む。
2. そのRQでcommit済みの最大Investigation versionを探す。
3. 次の整数versionを3桁0埋めで採番する。
4. Investigationをdraftとして作成する。
5. `00_context` をvalidかつ明示的にfrozenになるまで整える。
6. freeze後のcontext-defining semantic changeは次versionへ送る。
7. historical Investigationをrenumberしない。

例:

`RQ-0007-v001` と `RQ-0007-v002` が存在する場合、v002が途中でabandonされていても次は `RQ-0007-v003` とする。

## 11. Decision table

| 変更 | Draft context | Frozen context | RQ identity |
| --- | --- | --- | --- |
| 文法のみのwording修正 | 同一version | frozen snapshotを維持し書換えない | 同一RQ |
| 意味同一のwording改善 | 同一version | 新実行では次version | 同一RQ |
| semantic question identity変更 | 新RQ | 新RQ | 新RQ |
| Scope変更 | 同一version | 次version | 通常は同一RQ |
| Question Type変更 | 同一version | 次version | 同一RQ |
| unknown Scope / Significanceの補完 | 同一version | frozen snapshot維持。新実行に必要なら次version | 同一RQ |
| result accept前のEvidence追加・修正 | 同一version | 同一version | 同一RQ |
| accepted result後の実質的Evidence追加 | N/A | 次version | 同一RQ |
| rendering / validator refactorのみ | 同一version | 同一version | 同一RQ |

## 12. Invariant

Investigation IDは次を意味する。

> prefixで示されるRQを、このversionでfreezeされたResearch Contextの下で実行したもの。

したがって、同じInvestigation IDが実質的に異なる2つのfrozen contextを指してはならない。
