# 都市伝説・怪談・現代伝承 分析軸体系 — 理論設計 v2

> **ステータス: THEORETICAL DESIGN / v2**  
> **旧版:** `urban_legend_16_axes_theoretical_design_v1.md`  
> **分析単位:** 1行 = 1伝承エントリ  
> **現行候補:** 21分析軸  
>
> 本文書は「16軸」という数を維持することを目的としない。  
> 1伝承エントリを比較可能な観察単位として、各分析変数が意味論的にも統計的にも独立した情報を持つよう、旧16軸を分解・再構成した理論設計である。

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

したがって、本体系は「怪異の種類」を分類するものではなく、**意味形成モデルの構造を分解して比較するための変数体系**である。

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

つまり、**人物数ではなく「世界のルール」が変わる場合**にEntryを分ける。

---

# 2. 分析軸とメタデータを分離する

以下は分析軸ではなく、レコード管理用メタデータとする。

| メタデータ | 用途 |
|---|---|
| Entry_ID | 1行を一意に識別 |
| Family_ID | 同一伝承ファミリ内の異伝・版を関連付ける |
| Entry_Type | 物語／命題型噂／俗信・ジンクス／体験モチーフ／流言イベント等 |
| Version_Scope | 今回どの版・時期・媒体範囲をコードするか |
| Source / Evidence | コード根拠 |
| Evidence_Rank | 典拠確度 |
| Coding_Status | D=明示 / I=推定 / U=不明 / NA=非該当 / C=競合 |
| Coding_Memo | 判定根拠・異伝差・保留事項 |
| Narrative_Time | 物語型Entryにのみ必要な補助メタデータ |

**Entry_Typeは分析単位の形式であり、比較軸ではない。**

---

# 3. データ構造の基本原則

## 3.1 Tidy data原則

本研究では、1伝承エントリを1行、1分析変数を1列として保持することを基本とする。

ただし階層コードは、1つの概念軸を複数列で表現する。

> **概念軸 ≠ Excel列数**

親コード・子コード・主コード・副コードを1セルの文字列へ詰め込まない。

---

## 3.2 分析軸のデータ型

各軸は次の5型のいずれかとして設計する。

| 型 | 名称 | 意味 |
|---|---|---|
| **S** | Single nominal | 排他的な1値 |
| **O** | Ordinal | 排他的な1値。順序あり |
| **H1** | Hierarchical single | 子コード1値。親は子から自動導出 |
| **H3** | Hierarchical primary-secondary | 主1値＋副0–2値。各親は子から自動導出 |
| **B** | Binary vector | 独立した複数Yes/No列 |

---

## 3.3 H3のcardinality

H3では次を厳守する。

### 主コード

- 必ず1つだけ
- 当該軸について伝承エントリを最も強く規定する値
- 主が2つ以上という状態は許可しない

### 副コード

- 0〜2個
- 順不同
- 主だけでは失われる独立した構造的役割がある場合のみ付与
- 単なる背景情報は副にしない

数学的には副コード集合を

`S = {c1, c2}, |S| <= 2`

として扱う。

Excel保存上は `secondary_1`, `secondary_2` の2列に展開するが、**意味上の順位はない**。

保存時はchild code ID順にcanonical sortする。

---

## 3.4 Parent / Child規則

親コードと子コードは分類粒度、主／副はEntry内の重要度であり、直交する。

### 必須規則

1. child → parent は一意のmany-to-one写像
2. 同一childが複数parentへ所属することを禁止
3. parentは原則として手入力しない
4. parent列はchildからlookupで自動導出する
5. 統計比較の標準粒度はparent
6. childは精密記述・下位分析用

例:

```text
A13_primary_child  = M01_PHYSICAL_ATTACK
A13_primary_parent = PHYSICAL_MATERIAL_EFFECT   # derived
```

---

# 4. 情報量を意識したコード体系設計

## 4.1 Parentコードの役割

Parentは406件規模の母集団で、**比較・集計・エントロピー分析に使う一次カテゴリ**とする。

事前設計上の目安は概ね **4〜9 Parent** とする。

これは固定ルールではない。パイロット後に実測分布で再設計する。

## 4.2 Childコードの役割

ChildはParent内の意味差を保持するために用いる。

- Parentより多くてよい
- ただしchildをEntry IDのように細分化しない
- 1 childが数件しか現れない場合でも、理論上重要なら保持可能
- 分析ではchild prevalenceや共起を別途見る

## 4.3 エントロピー評価

Parent primary codeについて、パイロット後に少なくとも以下を測る。

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
- 軸間冗長性

**コード値数そのものを最大化しない。** Entry_IDのように全件を完全識別する変数はentropyが高くても研究的意味を持たない。

---

# 5. v2で採用する21分析軸

旧16軸の複合軸を分解した結果、現時点では21軸となる。

| # | 軸 | 型 | 中心質問 | Parent目安 |
|---:|---|---|---|---:|
| 1 | 生成年代 | O | いつ成立したか | 8–9 |
| 2 | 初期媒体 | H1 | 最初にどの媒体で伝わったか | 5–7 |
| 3 | 現行・主要流通媒体 | H3 | 現在／主要期にどの媒体で流通するか | 5–7 |
| 4 | 生成・変容パターン | H3 | 時間とともにどう変形したか | 6–8 |
| 5 | 提示形式 | H3 | どんなコミュニケーション形式で提示されるか | 5–7 |
| 6 | 真実性提示 | S | どんな「本当らしさ」を要求するか | 6–8 |
| 7 | 意味形成対象 | H3 | 何が不可解・不確実なのか | 7–9 |
| 8 | 意味形成契機 | H3 | 何を手掛かりに問題化されるか | 5–7 |
| 9 | 意味付与操作 | H3 | 不可解なものをどう理解可能にするか | 6–9 |
| 10 | 因果源存在論 | H3 | 原因を何として世界に置くか | 6–8 |
| 11 | 発動・接触条件 | H3 | 何を契機に因果系へ入るか | 6–8 |
| 12 | 作用対象 | H3 | 誰／何に作用するか | 6–8 |
| 13 | 作用機構 | H3 | 因果源が対象へ何をするか | 8–9 |
| 14 | 帰結極性 | S | 結果は正・負・中立・混合か | 4 |
| 15 | 帰結領域 | H3 | 何の領域が最終的に変わるか | 6–9 |
| 16 | 作用時間構造 | H3 | 作用は時間上どう展開するか | 5–7 |
| 17 | 回避・制御方式 | H3 | 結果をどう回避・制御・利用できるか | 6–8 |
| 18 | 作用レイヤー | B | 因果効力は伝承内／受容者／社会現実のどこに及ぶか | 3 binary |
| 19 | 流通範囲 | H3 | 誰の間に伝承が流通するか | 5–7 |
| 20 | 特権情報保持者 | H3 | 誰が真相・追加情報を持つか | 5–7 |
| 21 | 現実アンカー | O | 実在世界へどの程度固定されるか | 5 |

---

# 6. Block A — 社会的成立・流通

## Axis 1 — 生成年代

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

現代に再流通した古伝承を「2020年代生成」としない。再燃はAxis 4。

---

## Axis 2 — 初期媒体

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

## Axis 3 — 現行・主要流通媒体

### 型

H3

### 目的

Entryが**現在または主要な流通期にどのメディア環境で再生産されるか**を見る。

Axis 2と同じ媒体taxonomyを共有できる。

### 理論上の意義

`初期媒体 != 現行媒体` の差が媒体移行を示す。

---

## Axis 4 — 生成・変容パターン

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

Axis 2–3は「どの媒体か」、Axis 4は「どう変わったか」。

---

## Axis 5 — 提示形式

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

## Axis 6 — 真実性提示

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

## Axis 7 — 意味形成対象

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

## Axis 8 — 意味形成契機

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

## Axis 9 — 意味付与操作

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

## Axis 10 — 因果源存在論

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

## Axis 11 — 発動・接触条件

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

## Axis 12 — 作用対象

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

## Axis 13 — 作用機構

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

## Axis 14 — 帰結極性

### 型

S

### 値

- 負
- 中立
- 正
- 混合

作用が非該当ならNA。

---

## Axis 15 — 帰結領域

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

## Axis 16 — 作用時間構造

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

## Axis 17 — 回避・制御方式

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

## Axis 18 — 作用レイヤー

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

## Axis 19 — 流通範囲

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

## Axis 20 — 特権情報保持者

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

## Axis 21 — 現実アンカー

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

# 10. 物理Excelスキーマ

## 10.1 S / O

```text
A06_value
A06_status
```

## 10.2 H1

```text
A02_child
A02_parent        # derived
A02_status
```

## 10.3 H3

```text
A13_primary_child
A13_primary_parent       # derived
A13_secondary1_child
A13_secondary1_parent    # derived
A13_secondary2_child
A13_secondary2_parent    # derived
A13_status
```

secondary1/2は意味上unordered。保存時のみcode ID順。

## 10.4 B

```text
A18_L1
A18_L2
A18_L3
A18_status
```

---

# 11. 統計分析時の標準表現

## 11.1 基本分布

各H3軸ではまず `primary_parent` を一次分析変数とする。

これによりParentレベルでShannon entropy等を計算する。

## 11.2 Secondaryの扱い

副コード集合全体を新しいカテゴリとして扱わない。

禁止例:

```text
M1+M3
M1+M21
M3+M21
M1+M3+M21
```

をそれぞれ別カテゴリ化する。

代わりに、各Parent/Childについて

- primary prevalence
- secondary prevalence
- any-position prevalence
- pairwise co-occurrence

を分析する。

## 11.3 ParentとChild

- Parent: 母集団比較・主要統計
- Child: 精密記述・局所比較

この二層化により、情報を失わずにスパース化を抑える。

---

# 12. 軸間の境界規則

## Axis 7 vs 8

- Axis 7 = **何が不可解なのか**
- Axis 8 = **何を手掛かりに不可解だと考えるのか**

## Axis 8 vs 21

- Axis 8 = 意味形成で利用される証拠・徴候
- Axis 21 = 伝承モデル全体が現実世界にどれだけ固定されるか

## Axis 9 vs 10

- Axis 9 = **どう説明するかという認知操作**
- Axis 10 = **何を原因として置くか**

例:

`S=原因帰属` と `N=企業・制度` は別変数。

## Axis 11 vs 13

- Axis 11 = 何が発動条件か
- Axis 13 = 発動後、何をするか

## Axis 12 vs 18

- Axis 12 = 誰／何が作用対象か
- Axis 18 = その作用が伝承内・受容者・社会現実のどのレイヤーに属するか

## Axis 13 vs 15

- Axis 13 = 動詞
- Axis 15 = 最終状態

`M=物理攻撃` → `Outcome=死亡` を分離する。

## Axis 19 vs 20

- Axis 19 = 誰の間で噂が流通するか
- Axis 20 = 誰が追加情報・真相を持つか

---

# 13. 旧v1からの主要変更

## 13.1 軸数固定を撤回

16軸という数を目的化せず、複合軸を原子的な分析変数へ分解した結果21軸となった。

## 13.2 複合軸を分解

### 旧Axis 1 来歴・生成変容史

→ 生成年代 / 初期媒体 / 現行媒体 / 生成変容パターン

### 旧Axis 2 伝達・提示形式

→ 媒体をAxis 2–3へ、提示形式をAxis 5へ

### 旧Axis 11 帰結

→ 帰結極性 / 帰結領域

### 旧Axis 15 情報・認識分布

→ 流通範囲 / 特権情報保持者

## 13.3 作用対象ごとの子レコード化を禁止

1Entry = 1行を維持する。

## 13.4 文字列multi-labelを廃止

`N2+N8` や `M1+M21` のように1セルへ結合しない。

H3の固定列へ分解する。

## 13.5 主・副cardinalityを正式化

- 主 = exactly 1
- 副 = 0–2
- 副はunordered

## 13.6 Parentはderived variable化

parentとchildを双方手入力しない。

---

# 14. ストレステスト

## 14.1 猿夢

1Entryのまま保持する。

例:

- A07意味形成対象: 主=異常体験、副=未知存在
- A10因果源: 主=空間／世界、副=人格怪異または正体不明存在
- A12作用対象: 主=他登場人物、副=主人公
- A13作用機構: 主=身体・物質作用(M1物理攻撃)、副=関係操作(M3標的化), 関係操作(M21再発)
- A15帰結領域: 主=身体、副=精神・認知
- A18: L1=1

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

`Axis 7 × Axis 10`

## RQ2

意味形成対象によって、使われる意味付与操作は変わるか。

`Axis 7 × Axis 9`

## RQ3

どの伝承が単なる説明を超え、行動規則・回避規則を提供するか。

`Axis 9 × Axis 11 × Axis 17`

## RQ4

超自然怪談と非超自然都市伝説は、因果源が違っても作用・制御構造を共有するか。

`Axis 10 × Axis 13 × Axis 17`

## RQ5

媒体変化によって、提示形式・真実性・意味形成構造は変化するか。

`Axis 1–6 × Axis 7–17`

## RQ6

伝承は伝承内部だけで完結するか、受容者や現実社会まで因果系へ取り込むか。

`Axis 18`

## RQ7

現実アンカーや情報非対称性は、どの因果モデルと結びつくか。

`Axis 19–21 × Axis 10/13`

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

この検証により、21軸という数も再度増減してよい。

---

# 18. 暫定結論

本研究の分析体系は、軸数を固定することではなく、

> **1伝承エントリ = 1意味形成モデル**

を、相互にできるだけ独立した情報変数へ分解することを目的とする。

現時点の最適な理論候補は21軸である。

そのうち階層型軸では、

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

