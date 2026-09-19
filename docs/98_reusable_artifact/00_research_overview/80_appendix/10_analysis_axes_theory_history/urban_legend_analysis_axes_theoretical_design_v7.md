# 都市伝説・怪談・現代伝承 分析次元体系 — 理論設計 v3

> **ステータス: THEORETICAL DESIGN / v3**  
> **旧版:** `urban_legend_analysis_axes_theoretical_design_v2.md`  
> **分析単位:** 1行 = 1伝承エントリ  
> **現行理論モデル:** 21概念次元  
>
> 本文書では、**概念次元（theoretical dimension）** と **保存フィールド（storage field）** を明確に分離する。  
> H1/H3でParent・Child、Primary・Secondaryの列が増えても、理論上の次元数は増えない。

---

# 0. 研究目的

本研究が直接明らかにしようとするのは、次である。

> **異常・不可解・不確実・偶然・危険・不可視な制度その他の意味形成を要求する対象に対して、人々のあいだで流通する伝承が、どのような手掛かりを用い、どのような説明・因果・規則・予測・対処を与え、それをどのように共有可能な世界モデルへ変換しているか。**

ここでいう「世界モデル」は、精密な因果理論に限らない。

- 「あれは幽霊だ」という命名
- 「会社が意図的に壊れるよう設計している」という原因帰属
- 「20歳まで覚えていると死ぬ」という条件付き予測
- 「逆回りしてはいけない」という禁忌化
- 「このメールを転送しないと不幸になる」という行動規則
- 「血液型によって性格が違う」という属性類型化

を含む。

したがって、本体系は「怪異の種類」を分類するものではなく、**意味形成モデルの構造を分解して比較するための理論次元体系**である。

---

# 1. 観察単位: 伝承エントリ

## 1.1 定義

> **伝承エントリとは、人々が異常・不可解・不確実な何かを理解可能なものへ変換するために共有する、独立して伝達可能な最小の意味形成モデルである。**

1伝承エントリをExcelの1行とする。

### 行を増やさないもの

- 登場人物が複数いる
- 被害者が複数いる
- 因果源が複数ある
- 作用が複数ある
- 帰結が複数ある
- 典拠が複数ある
- 同一構造の軽微な地域異伝がある

### 別Entryを検討するもの

同じFamily内でも、次の意味形成核が安定して変化している場合。

- 何を説明しているか
- 何を原因として置くか
- 何を発動条件とするか
- 何にどのように作用するか
- どのような帰結・回避規則を持つか

つまり、**人物数や作用数ではなく「世界のルール」が変わる場合**にEntryを分ける。

---

# 2. 三層モデル: 理論・コーディング・分析

v2では「分析軸」と「Excel列」の関係が曖昧であった。v3では次の三層を分離する。

## 2.1 理論層 — Conceptual Dimensions

研究上、互いに区別して問う概念的な次元。

例:

- 因果源存在論
- 作用機構
- 作用対象
- 現実アンカー

**現時点では21次元。**

Parent/ChildやPrimary/Secondaryは、この数を増やさない。

## 2.2 コーディング層 — Atomic Coding Fields

コーダーが実際に入力する原子的な値。

例: Dimension 13「作用機構」がH3なら、入力するのは原則として

```text
D13_primary_child
D13_secondary1_child
D13_secondary2_child
D13_status
```

である。

`secondary1` と `secondary2` は保存位置にすぎず、**意味上は順不同集合**である。

## 2.3 分析層 — Derived Analysis Fields

Childから自動導出し、集計・entropy・比較に用いる値。

```text
D13_primary_parent       = f(D13_primary_child)
D13_secondary1_parent    = f(D13_secondary1_child)
D13_secondary2_parent    = f(D13_secondary2_child)
```

Parentはコーダーが独立に判断する値ではない。

> **Parent = Childの粗視化（coarse-graining）**

である。

---

# 3. 「次元」と「列」を区別する

## 3.1 基本原則

> **21概念次元 ≠ 21 Excel列**

階層分類・主副関係・binary vectorを原子的な列へ展開するため、物理列数は21より多くなる。

しかし列が増えても、その列が同じ研究質問の異なる表現なら、新しい理論次元とは数えない。

### 例: Dimension 13 作用機構

```text
主作用 = M1 物理攻撃
副作用 = {M3 標的化, M21 再発・付着}
```

これは3次元ではない。すべて

> **「因果源は対象へ何をするか」**

という1つの概念次元に対する複合値である。

数学的にはH3次元を

```text
X_d = (p, S)
p = primary child, exactly 1
S = unordered set of secondary children, 0 <= |S| <= 2
```

として扱う。

## 3.2 ParentとChildは独立変数ではない

childからparentが一意に決まるなら、

```text
Parent = f(Child)
```

であり、

```text
H(Parent | Child) = 0
```

である。

したがってParent entropyとChild entropyを加算して「この次元はそれだけ多くの情報を持つ」と評価してはならない。

Parentは同一次元を粗い解像度で観測した値、Childは細かい解像度で観測した値である。

## 3.3 PrimaryとSecondaryも別次元ではない

Primary/Secondaryは、同一次元内部での構造的重要度を表す。

- Primary = その次元についてEntryを最も強く規定する値
- Secondary = Primaryだけでは失われる独立した追加構造

Secondaryが2個あるからといって、次元数を3倍にはしない。

---

# 4. メタデータと概念次元を分離する

以下は概念次元ではなく、レコード管理・証拠管理用メタデータとする。

| メタデータ | 用途 |
|---|---|
| Entry_ID | 1行を一意に識別 |
| Family_ID | 同一伝承ファミリ内の異伝・版を関連付ける |
| Entry_Type | 物語／命題型噂／俗信・ジンクス／体験モチーフ／流言イベント等 |
| Version_Scope | 今回どの版・時期・媒体範囲をコードするか |
| Source / Evidence | コード根拠 |
| Evidence_Rank | 典拠確度 |
| Entry_Workflow_Status | 未着手 / コーディング中 / レビュー待ち / 確定等、行全体の作業状態 |
| Entry_Coding_Memo | 行全体の判定根拠・異伝差・保留事項 |
| Narrative_Time | 物語型Entryにのみ必要な補助メタデータ |

**Entry_Typeは分析単位の形式であり、21概念次元には数えない。**

### 次元ごとの判定状態

各概念次元は、値とは別に `Dxx_status` を持つ。

- `D` = 典拠に直接明示
- `I` = 規則に基づく推定
- `U` = 資料不足で不明
- `NA` = そのEntryには構造上非該当
- `C` = 同一Version Scope内で競合

これはEntry全体のworkflow statusとは別である。

---

# 5. データ型の理論定義

各概念次元は次の5型のいずれかとして実装する。

| 型 | 名称 | 理論上の値 | コーディング入力 | 派生分析値 |
|---|---|---|---|---|
| **S** | Single nominal | 排他的1値 | value | なし |
| **O** | Ordinal | 排他的1値・順序あり | value | 必要なら数値化 |
| **H1** | Hierarchical single | child 1値 | child | parent=f(child) |
| **H3** | Hierarchical primary-secondary | primary 1 + secondary 0–2 | child×最大3 | parent×最大3 |
| **B** | Binary vector | 独立した複数bit | 各bit | 組合せ・合計等 |

## 5.1 H1

H1は**1概念次元**である。

```text
child = 1値
parent = f(child)
```

Excelで2列使っても、次元数は1。

## 5.2 H3

H3も**1概念次元**である。

### Primary

- exactly 1
- 当該次元でEntryを最も強く規定する値

### Secondary

- 0–2
- unordered
- Primaryだけでは失われる独立した構造がある場合のみ
- 背景情報は入れない

保存時のみchild code ID順にcanonical sortする。

## 5.3 B

Bは複数列を使うが、同じ理論質問の独立bitを持つ1概念次元である。

Dimension 18「作用レイヤー」の例:

```text
D18_L1_internal
D18_L2_receiver
D18_L3_social_reality
```

3列だが1次元。

---

# 6. 情報量評価の原則

## 6.1 標準entropy対象

H1/H3次元では、母集団レベルの一次比較は原則として

```text
primary_parent
```

を使う。

H1では単に `parent` を使う。

## 6.2 詳細entropy

必要に応じて `primary_child` のentropyも計算する。

Parent entropyとChild entropyは**別解像度の同じ次元**であり、合算しない。

## 6.3 Secondaryの評価

Secondary集合全体を1カテゴリにしない。

代わりに、各コードについて

- primary prevalence
- secondary prevalence
- any-position prevalence
- pairwise co-occurrence
- secondary_count

を見る。

## 6.4 H3全体の情報量

H3の完全な値は理論上 `(p,S)` だが、その全組合せを名義カテゴリ化すると組合せ爆発を起こす。

したがって、研究の標準統計ではH3全組合せentropyを使わない。

## 6.5 次元保持の判断

各Parent primary variableについてパイロット後に少なくとも以下を確認する。

- `K_declared`
- `K_observed`
- Shannon entropy `H`
- normalized entropy `H / log2(K)`
- effective category count `K_eff = 2^H`
- `K_eff / K_declared`
- rare code率
- U率
- NA率
- intercoder agreement
- 次元間冗長性

**コード値数そのものを最大化しない。**

---

# 7. v3で採用する21概念次元

旧16軸の複合軸を分解した結果、現時点では21概念次元となる。

| # | 概念次元 | 型 | 中心質問 | 標準分析表現 | Parent目安 |
|---:|---|---|---|---|---:|
| 1 | 生成年代 | O | いつ成立したか | value | 8–9 |
| 2 | 初期媒体 | H1 | 最初にどの媒体で伝わったか | parent / child | 5–7 |
| 3 | 現行・主要流通媒体 | H3 | 現在／主要期にどの媒体で流通するか | primary_parent | 5–7 |
| 4 | 生成・変容パターン | H3 | 時間とともにどう変形したか | primary_parent | 6–8 |
| 5 | 提示形式 | H3 | どんなコミュニケーション形式で提示されるか | primary_parent | 5–7 |
| 6 | 真実性提示 | S | どんな「本当らしさ」を要求するか | value | 6–8 |
| 7 | 意味形成対象 | H3 | 何が不可解・不確実なのか | primary_parent | 7–9 |
| 8 | 意味形成契機 | H3 | 何を手掛かりに問題化されるか | primary_parent | 5–7 |
| 9 | 意味付与操作 | H3 | 不可解なものをどう理解可能にするか | primary_parent | 6–9 |
| 10 | 因果源存在論 | H3 | 原因を何として世界に置くか | primary_parent | 6–8 |
| 11 | 発動・接触条件 | H3 | 何を契機に因果系へ入るか | primary_parent | 6–8 |
| 12 | 作用対象 | H3 | 誰／何に作用するか | primary_parent | 6–8 |
| 13 | 作用機構 | H3 | 因果源が対象へ何をするか | primary_parent | 8–9 |
| 14 | 帰結極性 | S | 結果は正・負・中立・混合か | value | 4 |
| 15 | 帰結領域 | H3 | 何の領域が最終的に変わるか | primary_parent | 6–9 |
| 16 | 作用時間構造 | H3 | 作用は時間上どう展開するか | primary_parent | 5–7 |
| 17 | 回避・制御方式 | H3 | 結果をどう回避・制御・利用できるか | primary_parent | 6–8 |
| 18 | 作用レイヤー | B | 因果効力は伝承内／受容者／社会現実のどこに及ぶか | binary vector | 3 bits |
| 19 | 流通範囲 | H3 | 誰の間に伝承が流通するか | primary_parent | 5–7 |
| 20 | 特権情報保持者 | H3 | 誰が真相・追加情報を持つか | primary_parent | 5–7 |
| 21 | 現実アンカー | O | 実在世界へどの程度固定されるか | value | 5 |

## 7.1 型別の次元数

- O: 2次元
- S: 2次元
- H1: 1次元
- H3: 15次元
- B: 1次元

合計 **21概念次元**。

## 7.2 物理列数の概算

完全にmaterializeしたwide analysis tableでは、21次元よりはるかに多くの列を持つ。

- O/S: 4 value列
- H1: child + derived parent = 2列
- H3: 15次元 × 6 value列 = 90列
- B: 3 binary列
- status: 21列

合計は概ね **120分析関連列**（メタデータ除外）。

これは「120分析軸」を意味しない。

実運用では、入力シートと分析ビューを分けてよい。

- **Coding Input View**: コーダーはChildとstatusのみ入力
- **Analysis View**: Parentをlookupでmaterializeして集計・entropy分析に使用

---

# 6. Block A — 社会的成立・流通

## Dimension 1 — 生成年代

### 型

O

### 目的

伝承エントリの**最古の識別可能な形**が成立した時期を比較する。

### 暫定値

- 前近代
- 明治〜大正
- 昭和戦前
- 1945–1969
- 1970年代
- 1980年代
- 1990年代
- 2000年代
- 2010年代
- 2020年代以降

実測分布を見て隣接年代を統合する。

### 注意

現代に再流通した古伝承を「2020年代生成」としない。再燃はDimension 4。

---

## Dimension 2 — 初期媒体

### 型

H1

### 目的

最初に確認できる流通回路を測る。

### Parent候補

- ORAL_LOCAL — 口承・ローカル伝承
- PRINT_CORRESPONDENCE — 手紙・新聞・雑誌・書籍
- BROADCAST — ラジオ・テレビ
- EARLY_DIGITAL_TEXT — パソコン通信・BBS・Eメール
- OPEN_WEB_SOCIAL — Web・掲示板・SNS
- AUDIOVISUAL_DIGITAL — 動画・配信
- INSTITUTIONAL_RECORD — 公文書・報告書等を起点とする特殊型

Childは学校内伝承、職場内伝承、新聞、雑誌、BBS、SNS等。

---

## Dimension 3 — 現行・主要流通媒体

### 型

H3

### 目的

Entryが**現在または主要な流通期にどのメディア環境で再生産されるか**を見る。

Dimension 2と同じ媒体taxonomyを共有できる。

### 理論上の意義

`初期媒体 != 現行媒体` の差が媒体移行を示す。

---

## Dimension 4 — 生成・変容パターン

### 型

H3

### Parent候補

- STABILITY — 単発固定・低変異
- VARIATION — 口承変異・再話・定型化・増補
- MEDIA_MIGRATION — 媒体移行・ネット再増幅
- COLLABORATIVE_PRODUCTION — 実況共同生成・複数投稿者・シリーズ化
- MEDIA_EXPANSION — メディアミックス
- RECONTEXTUALIZATION — 実事件への付着・再燃・再文脈化
- CONTESTATION — 検証・反証を伴う再流通・起源喪失

### 境界

Dimension 2–3は「どの媒体か」、Dimension 4は「どう変わったか」。

---

## Dimension 5 — 提示形式

### 型

H3

### Parent候補

- EXPERIENCE_NARRATIVE — 体験談・回想
- HEARSAY_NARRATIVE — FOAF・地元伝承・職場伝承
- DOCUMENTARY_RECORD — ログ・日誌・新聞風・記録
- PROPOSITIONAL_CLAIM — 命題型主張・俗説
- RULE_WARNING_INSTRUCTION — 警告・ジンクス・儀式・手順
- COLLECTIVE_HYBRID — 実況・複数証言・複合形式

---

## Dimension 6 — 真実性提示

### 型

S

### 暫定値

- 直接体験として主張
- 身近な伝聞として主張
- 共同体で既知の事実として主張
- 一般事実・制度・科学的事実として主張
- 条件付き・蓋然的信念として提示
- 真偽未確定として提示
- 否定・反証と併存
- 虚構起源が既知だが伝承として再流通

### 注意

研究者が真偽判定する軸ではない。

---

# 7. Block B — 意味形成

## Dimension 7 — 意味形成対象

### 型

H3

### 目的

> **この伝承がなければ、何が説明されないまま残るのか。**

本研究の中心軸。

### Parent候補

- ANOMALOUS_EXPERIENCE_EXISTENCE — 異常体験・未知存在
- DEATH_CHANCE_MISFORTUNE — 死・喪失・偶然・不運
- PLACE_SPACE_ENVIRONMENT — 場所・空間・環境の異常／危険
- INTERPERSONAL_CRIME_THREAT — 対人・犯罪脅威
- BODY_HEALTH_FOOD — 身体・健康・食品リスク
- TECHNOLOGY_PRODUCT_SYSTEM — 技術・製品・システムの不可解
- INSTITUTION_ORGANIZATION — 制度・組織の不透明性
- IDENTITY_NORM_GROUP — 人格差・属性・規範・内外集団
- INFORMATION_SOCIAL_UNCERTAINTY — 情報空白・不足・集団不安

Childで「死後」「スポーツ上の不運」「海外犯罪」「性格差」等を区別する。

---

## Dimension 8 — 意味形成契機

### 型

H3

### 目的

何を徴候・証拠として「説明すべき問題」が立ち上がるか。

### Parent候補

- DIRECT_EXPERIENCE — 直接経験・身体感覚
- SOCIAL_TESTIMONY — 他者証言・口コミ
- PATTERN_CORRELATION — 反復・偶然・経験則・疑似統計
- MATERIAL_RECORD_TRACE — 写真・録音・文書・物的痕跡
- EVENT_HISTORY_PLACE_TRACE — 実事件・事故・災害・地名・歴史痕跡
- TECHNICAL_INSTITUTIONAL_OPACITY — 不具合・非公開性・制度空白
- CLAIM_FIRST — 手掛かりなし／命題先行

---

## Dimension 9 — 意味付与操作

### 型

H3

### 目的

不可解な入力を**どんな認知・社会的操作で理解可能にするか**。

### Parent候補

- CATEGORIZATION — 命名・カテゴリー化
- CAUSAL_ATTRIBUTION — 原因帰属
- AGENCY_INTENTION — 主体・意図帰属
- PATTERN_PREDICTION — パターン化・相関化・予兆・予測
- NORMATIVE_VALUATION — 吉凶化・道徳化・禁忌化
- CONTROL_RULE_FORMATION — 対処・制御・手順化
- SOCIAL_SYSTEM_INTERPRETATION — 陰謀化・社会的境界化・制度説明
- HISTORICIZATION — 由来化・歴史化
- PRESERVED_UNKNOWABILITY — 空白・不可知性の保持

---

## Dimension 10 — 因果源存在論

### 型

H3

### 目的

伝承が原因を**何として世界に置くか**。

### Parent候補

- HUMAN_SOCIAL_ACTOR — 人間・共同体・組織
- SUPERNATURAL_AGENT — 人格怪異・神格・超越主体
- ANOMALOUS_LIVING_INTERNAL — 未知生物・寄生体・身体内部存在
- OBJECT_INFORMATION — 呪物・人工物・情報・記号
- PLACE_SPACETIME — 場所・空間・世界
- NATURAL_BIOPHYSICAL_PROCESS — 自然・物理・生物学的属性／過程
- PHENOMENON_EXPERIENCE — 独立主体を仮定しない現象・体験

旧NコードはChild候補として再配置する。

---

# 8. Block C — 因果・行動モデル

## Dimension 11 — 発動・接触条件

### 型

H3

### Parent候補

- SENSORY_EXPOSURE — 見る・聞く・触る等
- INFORMATION_EXPOSURE — 知る・読む・記憶する等
- MANIPULATION_RITUAL — 開ける・所有する・儀式をする等
- MOVEMENT_SPATIAL_ENTRY — 乗る・降りる・入る・通る等
- SOCIAL_RELATION_TRANSACTION — 会う・雇われる・契約する等
- TIME_ATTRIBUTE_CONDITION — 時刻・年齢・属性・場所条件
- PASSIVE_OCCURRENCE — 発症・経験・巻き込まれる・受信する
- NO_CONTACT_REQUIRED — 接触不要

---

## Dimension 12 — 作用対象

### 型

H3

### Parent候補

- FOCAL_PERSON — 主人公・体験者
- OTHER_PERSON — 他登場人物・特定被害者
- KIN_CLOSE_RELATION — 家族・血縁・親密者
- GROUP_COMMUNITY — 集団・共同体・不特定人群
- ORGANIZATION_SYSTEM — 組織・制度
- OBJECT_TECH_DATA — 物体・設備・技術・データ
- PLACE_ENVIRONMENT_WORLD — 場所・環境・世界状態
- AUDIENCE_RECEIVER_PUBLIC — 語り手・読者・聞き手・次の受信者・一般社会

### 規則

主対象1、副対象0–2。別行に分解しない。

---

## Dimension 13 — 作用機構

### 型

H3

### 目的

因果源が対象へ**何をするか**。

### Parent候補

- MANIFESTATION — 顕現・追加作用なし
- PHYSICAL_MATERIAL_EFFECT — 身体・物体・環境の物理／生理変化
- RELATIONAL_TARGETING — 追跡・標的化・誘引・擬態・付着・他怪異との関係
- INTERNAL_CONTROL — 憑依・寄生・共生
- COGNITIVE_INFORMATION_EFFECT — 認知災害・精神干渉・記憶改変・情報誘導
- REALITY_SPACETIME_EFFECT — 現実・空間・時間の改変／置換
- PROPAGATION — 感染・伝播
- SOCIAL_INSTITUTIONAL_EFFECT — 隠蔽・排除・脅迫・制度的強制
- FATE_FORTUNE_EFFECT — 運命固定・吉凶付与

旧M0–M25はChild候補として再配置する。

### M0相当の厳格化

MANIFESTATIONは、十分な資料から**追加作用が構造上必須でない**と確認できる場合のみ。

`作用情報がない` をMANIFESTATIONへ入れない。

---

## Dimension 14 — 帰結極性

### 型

S

### 値

- 負
- 中立
- 正
- 混合

作用が非該当ならNA。

---

## Dimension 15 — 帰結領域

### 型

H3

### Parent候補

- BODY_HEALTH — 身体・健康
- MIND_COGNITION — 精神・認知
- SOCIAL_STATUS_RELATION — 社会関係・地位・信用
- MATERIAL_TECH_ECONOMIC — 物的・技術的・経済的
- BEHAVIOR_CHOICE — 行動・選択
- LIFE_COURSE_IDENTITY — 人生・将来・存在・アイデンティティ
- WORLD_KNOWLEDGE — 世界認識・知識・説明状態
- COLLECTIVE_SOCIAL_SYSTEM — 集団・社会・制度
- OPPORTUNITY_FORTUNE — 吉凶・機会・恋愛・合否等

Childで死亡、身体欠損、データ削除、買い占め等を記述する。

---

## Dimension 16 — 作用時間構造

### 型

H3

### Parent候補

- IMMEDIATE_SINGLE — 即時・単発観測
- DELAYED_DEADLINE_LATENT — 遅延・期限・潜伏
- PROGRESSIVE_CHRONIC — 段階進行・長期浸食・生涯
- RECURRENT_CYCLIC — 再発・周期
- CONTINUOUS_PURSUIT — 追跡・持続
- TRANSMISSIVE_INTERGENERATIONAL — 連鎖拡散・世代継承

---

## Dimension 17 — 回避・制御方式

### 型

H3

### Parent候補

- AVOIDANCE — 単純回避・逃走
- RULE_COMPLIANCE — ルール遵守・正答
- RITUAL_EXPERT_INTERVENTION — 儀式・専門家介入
- COST_TRANSFER_MANAGEMENT — 代償・転嫁・管理
- INFORMATION_TECHNICAL_CORRECTION — 情報検証・訂正・技術復旧
- USE_EXPLOITATION — 利用可能・願掛け等
- UNAVOIDABLE — 不可避
- NO_CONTROL_NEEDED — 回避不要

---

## Dimension 18 — 作用レイヤー

### 型

B

### 実装

3つの独立binary列。

- `L1_internal_model`
- `L2_receiver`
- `L3_social_reality`

### 定義

- **L1** — 伝承内容内部で人物・物体・環境等に作用
- **L2** — 話を読む・聞く・受信する現実側の受容者が伝承内容上の因果対象になる
- **L3** — 噂を信じた人間の行動等により現実社会で確認可能な結果が生じる

`L1+L2` のような文字列で保存しない。

---

# 9. Block D — 社会的埋め込み

## Dimension 19 — 流通範囲

### 型

H3

### Parent候補

- PRIVATE_INDIVIDUAL — 個人・ごく限定された経験者
- KIN_PEER — 家族・友人・学校仲間
- LOCAL_COMMUNITY — 地域共同体
- PROFESSIONAL_SPECIALIST — 職業・専門コミュニティ
- ORGANIZATIONAL_INTERNAL — 組織内部
- NETWORKED_PUBLIC — 掲示板・SNS・ネット群衆
- MASS_PUBLIC — 一般社会・全国流通

主流通範囲1、副0–2。

---

## Dimension 20 — 特権情報保持者

### 型

H3

### 目的

誰が**真相・追加ルール・隠された情報**を持つか。

### Parent候補

- NO_PRIVILEGE — 特権保持者なし
- PERSONAL_KIN — 当事者・家族
- LOCAL_PEER_INSIDER — 地元・学校・職場内部者
- EXPERT_PROFESSIONAL — 専門家・研究者・職人等
- ORGANIZATION_PERPETRATOR — 組織・加害者・権限主体
- INACCESSIBLE_UNKNOWN — 誰も知らない／失われた
- HAZARDOUS_INFORMATION — 情報自体が危険でアクセスが制約される

---

## Dimension 21 — 現実アンカー

### 型

O

### 値

0. 匿名・抽象
1. 一般的現実背景
2. 具体的実在対象
3. 実在制度・社会史がモデル成立条件
4. 史実・記録・既存伝承を因果構造へ統合

### 注意

典拠が現実に存在することと、伝承内容の現実アンカーは別。

---

# 10. 物理データスキーマ

物理スキーマは**概念次元の理論構造を忠実に保存する実装**であり、次元数そのものではない。

## 10.1 S / O

```text
D06_value
D06_status
```

1次元、value 1列。

## 10.2 H1

```text
D02_child
D02_parent        # derived = f(child)
D02_status
```

1次元、入力1列＋派生1列。

## 10.3 H3

```text
D13_primary_child
D13_primary_parent       # derived
D13_secondary1_child
D13_secondary1_parent    # derived
D13_secondary2_child
D13_secondary2_parent    # derived
D13_status
```

1次元、Child入力最大3列＋Parent派生最大3列。

`secondary1/2` は意味上unordered。保存時のみchild code ID順でcanonicalizeする。

## 10.4 B

```text
D18_L1
D18_L2
D18_L3
D18_status
```

1次元、3 binary field。

## 10.5 入力ビューと分析ビュー

### Coding Input View

人手入力の対象を最小化する。

- S/O: value
- H1: child
- H3: primary_child, secondary1_child, secondary2_child
- B: bit列
- 各次元: status

Parentは入力しない。

### Analysis View

Child→Parent対応表からParentを自動生成する。

- primary_parent
- secondary1_parent
- secondary2_parent

これにより、親子不整合を構造的に防止する。

---

# 11. 統計分析時の標準表現

## 11.1 次元数を数える単位

理論次元数は21。

Excel列数、Parent列数、Child列数、Secondary列数を理論次元数へ加算しない。

## 11.2 基本分布

H1/H3ではParentレベルを母集団比較の標準粒度とする。

H3では原則 `primary_parent` の分布を比較する。

## 11.3 Child分析

`primary_child` はParent内部の詳細構造を分析するときに使用する。

ParentとChildを同じモデルへ無批判に同時投入しない。ChildがParentを決定するため、強い冗長性を持つ。

## 11.4 Secondary分析

Secondaryは次元内の補助構造であり、独立次元ではない。

各コードについて

- primary prevalence
- secondary prevalence
- any-position prevalence
- pairwise co-occurrence
- secondary_count

を分析する。

## 11.5 H3の総合表現

個別Entryを記述するときは

```text
primary = M1
secondary = [M3, M21]
```

という概念表現を使ってよい。

ただしExcelではlist文字列にせずatomic columnsへ展開する。

## 11.6 情報量の二重計上禁止

以下を禁止する。

- `H(parent) + H(child)` を同一次元の総情報量とみなす
- primary / secondaryを別次元として数える
- ParentとChildを独立特徴量としてそのまま同じ解析へ投入する
- secondary集合の全組合せをカテゴリID化する

---

# 12. 次元間の境界規則

## Dimension 7 vs 8

- Dimension 7 = **何が不可解なのか**
- Dimension 8 = **何を手掛かりに不可解だと考えるのか**

## Dimension 8 vs 21

- Dimension 8 = 意味形成で利用される証拠・徴候
- Dimension 21 = 伝承モデル全体が現実世界にどれだけ固定されるか

## Dimension 9 vs 10

- Dimension 9 = **どう説明するかという認知操作**
- Dimension 10 = **何を原因として置くか**

例:

`S=原因帰属` と `N=企業・制度` は別変数。

## Dimension 11 vs 13

- Dimension 11 = 何が発動条件か
- Dimension 13 = 発動後、何をするか

## Dimension 12 vs 18

- Dimension 12 = 誰／何が作用対象か
- Dimension 18 = その作用が伝承内・受容者・社会現実のどのレイヤーに属するか

## Dimension 13 vs 15

- Dimension 13 = 動詞
- Dimension 15 = 最終状態

`M=物理攻撃` → `Outcome=死亡` を分離する。

## Dimension 19 vs 20

- Dimension 19 = 誰の間で噂が流通するか
- Dimension 20 = 誰が追加情報・真相を持つか

---

# 13. v2 → v3 の主要変更

## 13.1 「概念次元」と「保存フィールド」を分離

v2で導入した21概念次元を維持しつつ、Parent/Child・Primary/Secondaryによって増えるExcel列を新しい次元として数えないことを正式化した。

## 13.2 三層モデルを導入

理論層 / コーディング層 / 分析層を分離し、ParentをChildからのderived fieldとして定義した。

## 13.3 複合軸を分解

### 旧Dimension 1 来歴・生成変容史

→ 生成年代 / 初期媒体 / 現行媒体 / 生成変容パターン

### 旧Dimension 2 伝達・提示形式

→ 媒体をDimension 2–3へ、提示形式をDimension 5へ

### 旧Dimension 11 帰結

→ 帰結極性 / 帰結領域

### 旧Dimension 15 情報・認識分布

→ 流通範囲 / 特権情報保持者

## 13.4 作用対象ごとの子レコード化を禁止

1Entry = 1行を維持する。

## 13.5 文字列multi-labelを廃止

`N2+N8` や `M1+M21` のように1セルへ結合しない。

H3の固定列へ分解する。

## 13.6 主・副cardinalityを正式化

- 主 = exactly 1
- 副 = 0–2
- 副はunordered

## 13.7 Parentはderived variable化

parentとchildを双方手入力しない。

---

# 14. ストレステスト

## 14.1 猿夢

1Entryのまま保持する。

例:

- D07意味形成対象: 主=異常体験、副=未知存在
- D10因果源: 主=空間／世界、副=人格怪異または正体不明存在
- D12作用対象: 主=他登場人物、副=主人公
- D13作用機構: 主=身体・物質作用(M1物理攻撃)、副=関係操作(M3標的化), 関係操作(M21再発)
- D15帰結領域: 主=身体、副=精神・認知
- D18: L1=1

後代の「読者感染型」が独立した意味形成核として安定していれば別Entry化し、L2=1。

## 14.2 ひとりかくれんぼ

- 因果源: 主=物体・情報系の呪物child、副=超自然主体child
- 発動: 主=儀式・操作
- 対象: 主=実践者、副=物体／環境
- 作用: 主=身体・物質作用の環境物理作用child
- 回避: 主=規則遵守／儀式終了
- Layer: L1

## 14.3 ソニータイマー

- 意味形成対象: 技術・製品・システム
- 契機: 技術的不具合＋反復パターン
- 意味付与: 原因帰属＋主体意図帰属
- 因果源: HUMAN_SOCIAL_ACTORの企業／組織child
- 作用対象: 物体・技術
- 作用機構: 噂内容上は物理・機器作用
- 帰結: 物的・技術的・経済的
- Layer: L1。現実の購買行動が確認される場合のみL3

## 14.4 金縛り

「体験モチーフ」と「霊的原因説明」はFamily内でEntry分割候補。

- 体験モチーフEntry: 因果源=PHENOMENON_EXPERIENCE
- 霊的説明Entry: 因果源=SUPERNATURAL_AGENT

この差は意味形成核を変更するため、Entry分割に理論的意味がある。

## 14.5 トイレットペーパー不足流言

- 意味形成対象: INFORMATION_SOCIAL_UNCERTAINTY
- 意味付与: PATTERN_PREDICTION / RISK系child
- 因果源: OBJECT_INFORMATIONの情報child
- 対象: AUDIENCE_RECEIVER_PUBLIC
- 作用: COGNITIVE_INFORMATION_EFFECTの行動誘導child + PROPAGATION
- 帰結: BEHAVIOR_CHOICE + COLLECTIVE_SOCIAL_SYSTEM
- Layer: L3=1

---

# 15. この設計で直接分析できる研究問い

## RQ1

何の不確実性が、どの種類の原因モデルへ変換されやすいか。

`Dimension 7 × Dimension 10`

## RQ2

意味形成対象によって、使われる意味付与操作は変わるか。

`Dimension 7 × Dimension 9`

## RQ3

どの伝承が単なる説明を超え、行動規則・回避規則を提供するか。

`Dimension 9 × Dimension 11 × Dimension 17`

## RQ4

超自然怪談と非超自然都市伝説は、因果源が違っても作用・制御構造を共有するか。

`Dimension 10 × Dimension 13 × Dimension 17`

## RQ5

媒体変化によって、提示形式・真実性・意味形成構造は変化するか。

`Dimension 1–6 × Dimension 7–17`

## RQ6

伝承は伝承内部だけで完結するか、受容者や現実社会まで因果系へ取り込むか。

`Dimension 18`

## RQ7

現実アンカーや情報非対称性は、どの因果モデルと結びつくか。

`Dimension 19–21 × Dimension 10/13`

---

# 16. この段階で確定しないこと

本文書は理論設計であり、以下は次のコードブック設計で決める。

- Childコードの最終一覧
- Parent名の最終語彙
- include / exclude条件
- Primary選択の詳細判定フロー
- Secondary付与閾値
- Coding statusの軸別規則
- rare code統合基準
- intercoder disagreement処理

またParent数も現時点では仮説であり、パイロット分布により統合・分割する。

---

# 17. パイロット前の情報量監査方針

本適用前に、40–60件程度の層化パイロットを行い、各Parent primary variableについて確認する。

## 保持候補

- 複数値が実際に利用される
- `K_eff` が2以上
- 1カテゴリへの極端な集中がない
- U/NAが許容範囲
- 他軸と完全冗長でない
- コーダー一致が確保できる

## 再設計候補

- ほぼ1値しか取らない
- Parentが多いのに実効カテゴリ数が小さい
- rare categoryが大量に発生
- U/NAが多数
- 別軸とほぼ同じ情報を持つ
- 主コード選択が安定しない

この検証により、21概念次元という数も再度増減してよい。

---

# 18. 暫定結論

本研究の分析体系は、軸数を固定することではなく、

> **1伝承エントリ = 1意味形成モデル**

を、相互にできるだけ独立した情報変数へ分解することを目的とする。

現時点の最適な理論候補は21概念次元である。

そのうち階層型次元では、

> **主1 + 副最大2**

とし、ParentとChildを分離する。

- Parent = 比較・統計の標準粒度
- Child = 構造の精密記述
- 主 = Entryの中心構造
- 副 = 主だけでは失われる独立した追加構造

これにより、

- 1セルに複雑な文字列を詰め込まない
- 作用対象ごとに行を増殖させない
- 分布・エントロピーを直接計算できる
- Parent/Child両レベルで分析できる
- rareな構造をChildとして保持しつつParentでは十分な標本数を確保する

という条件を同時に満たす。

---

# 参考文献・方法論

- Krippendorff, K. (2019). *Content Analysis: An Introduction to Its Methodology*, 4th ed. SAGE. Unitizing / recording-coding / reliabilityを分析設計の独立工程として扱う。
- Wickham, H. (2014). “Tidy Data.” *Journal of Statistical Software*, 59(10), 1–23. DOI: 10.18637/jss.v059.i10. 1変数1列、1観察1行というデータ構造原則。
- Shannon, C. E. (1948). “A Mathematical Theory of Communication.” *Bell System Technical Journal*, 27, 379–423, 623–656. カテゴリ分布の情報量を評価する基礎。
- Weick, K. E., Sutcliffe, K. M., & Obstfeld, D. (2005). “Organizing and the Process of Sensemaking.” *Organization Science*, 16(4), 409–421.
- Bordia, P., & DiFonzo, N. (2004). “Problem Solving in Social Interactions on the Internet: Rumor as Social Cognition.” *Social Psychology Quarterly*, 67(1), 33–49.
- DiFonzo, N., & Bordia, P. (2007). “Rumor, Gossip and Urban Legends.” *Diogenes*, 54(1), 19–35.

