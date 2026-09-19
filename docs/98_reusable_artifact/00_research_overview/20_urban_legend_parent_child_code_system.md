**文書名:** 都市伝説・怪談・現代伝承 — Parent / Child コード体系設計 v1

> **ステータス: CODE TAXONOMY DESIGN / v1**  
> **対応理論設計:** `urban_legend_analysis_axes_theoretical_design_v3.md`  
> **分析単位:** 1行 = 1伝承エントリ  
> **目的:** 21概念次元を、Parent=比較用粗視化、Child=精密記述として実装可能なコード体系へ落とす。

---

# 1. 設計原則

## 1.1. Parent / Child

- Parentは406件規模の母集団比較・entropy分析に用いる粗粒度カテゴリ。
- Childは伝承構造を失わない詳細カテゴリ。
- H1/H3では **Child → Parent は必ず一意** とし、`Parent = f(Child)` を満たす。
- Parentはコーダーが手入力せず、Childから自動導出する。
- ParentとChildは同一次元の異なる解像度であり、独立次元として情報量を加算しない。

## 1.2. Primary / Secondary

- H3のPrimaryはexactly 1。
- Secondaryは0–2。意味上はunordered set。
- Excelでは`secondary1_child`,`secondary2_child`に分け、保存時のみcode ID順にcanonicalizeする。
- Secondaryは「少し関係する」ものを付けず、その要素を除くと意味形成モデルが実質的に変わる場合だけ付ける。

## 1.3. S/O/Bには階層を作らない

S/O/B型はフラット値またはbinary bitを使用する。Parent/Childを無理に導入しない。

## 1.4. コードID規則

H1/H3 Childは原則 `Dnn.PPP.CHILD`。Parentは`Dnn.PPP`。例: `D13.PHY.PHYSICAL_ATTACK` → Parent `D13.PHY`。
S/Oは `Dnn.CODE`。Bは `D18.L1` 等。ラベル変更時もIDは原則維持する。

## 1.5. 不明・非該当

`U / NA / C`はコード値に混ぜず、Dimension-level statusで保持する。したがって「その他」「不明」Childは原則作らない。新しい安定構造が既存Childへ入らない場合はコードブック改訂候補とする。

---

# 2. 事前粒度監査

| D | 概念次元 | 型 | Parent数 | Child/値数 | Child/Parent平均 | 事前判定 |
|---:|---|---|---:|---:|---:|---|
| 1 | 生成年代 | O | — | 9 | — | フラット値 |
| 2 | 初期媒体 | H1 | 7 | 28 | 4.00 | 適正候補 |
| 3 | 現行・主要流通媒体 | H3 | 7 | 28 | 4.00 | 適正候補 |
| 4 | 生成・変容パターン | H3 | 7 | 24 | 3.43 | 適正候補 |
| 5 | 提示形式 | H3 | 6 | 25 | 4.17 | 適正候補 |
| 6 | 真実性提示 | S | — | 7 | — | フラット値 |
| 7 | 意味形成対象 | H3 | 9 | 38 | 4.22 | 適正候補 |
| 8 | 意味形成契機 | H3 | 7 | 28 | 4.00 | 適正候補 |
| 9 | 意味付与操作 | H3 | 9 | 31 | 3.44 | 適正候補 |
| 10 | 因果源存在論 | H3 | 7 | 28 | 4.00 | 適正候補 |
| 11 | 発動・接触条件 | H3 | 8 | 34 | 4.25 | 適正候補 |
| 12 | 作用対象 | H3 | 8 | 23 | 2.88 | 適正候補 |
| 13 | 作用機構 | H3 | 9 | 33 | 3.67 | 適正候補 |
| 14 | 帰結極性 | S | — | 4 | — | フラット値 |
| 15 | 帰結領域 | H3 | 9 | 46 | 5.11 | 適正候補 |
| 16 | 作用時間構造 | H3 | 6 | 17 | 2.83 | 適正候補 |
| 17 | 回避・制御方式 | H3 | 8 | 26 | 3.25 | 適正候補 |
| 18 | 作用レイヤー | B | — | 3 | — | binary vector |
| 19 | 流通範囲 | H3 | 7 | 20 | 2.86 | 適正候補 |
| 20 | 特権情報保持者 | H3 | 7 | 19 | 2.71 | 適正候補 |
| 21 | 現実アンカー | O | — | 5 | — | フラット値 |

この表は**分布を見ない事前監査**である。実際の保持・統合はパイロット後に`K_observed`, Shannon entropy, `K_eff`, rare-code率, U/NA率, coder agreementを用いて再判定する。

---

# 3. v2変更要約

- D02: 最古確認流通媒体へ再定義。無根拠な口承推定を禁止。
- D03: 確認流通媒体ポートフォリオ（Version Scope）へ再定義。
- D16: 因果時間構造へ再定義し、STA/EVTを導入。Parent 6→7。

---

# 4. D01. 生成年代

**型:** `O`

**設計メモ:** 成立年の精密値は補助メタデータ Earliest_Attested_Year に保持し、本次元では比較用の粗い年代帯を使う。

| Value ID | 値 | 定義 |
|---|---|---|
| `D01.G0` | 前近代（〜1867） | 最古形が明治以前。 |
| `D01.G1` | 1868–1944 | 明治〜昭和戦前。 |
| `D01.G2` | 1945–1969 | 戦後直後〜高度成長前半。 |
| `D01.G3` | 1970年代 | 1970–1979。 |
| `D01.G4` | 1980年代 | 1980–1989。 |
| `D01.G5` | 1990年代 | 1990–1999。 |
| `D01.G6` | 2000年代 | 2000–2009。 |
| `D01.G7` | 2010年代 | 2010–2019。 |
| `D01.G8` | 2020年代以降 | 2020年以降。 |

---

# 5. D02. 最古確認流通媒体

**型:** `H1`

**v2定義:** 起源媒体を推測せず、現在の証拠から最も古く確認できる実際の流通回路をコードする。

Parent数: **7**

## 5.1. 証拠規則

- `D`: 同時代資料、原投稿、原メール、採録情報などが媒体を直接示す。
- `I`: 信頼できる後代資料が「学校で聞いた」「子どもの噂」「口コミで拡散」等、媒体を明示する。
- `U`: 最古確認媒体を特定できない。
- `ネット発祥=No`、伝説の古さ、Entry Typeだけから `口承` を推定してはならない。
- 後代の研究書・事典が存在するだけで `書籍` を最古媒体にしてはならない。

## 5.2. `D02.ORL` — 口承・限定共同体

| Child ID | Child | 定義 |
|---|---|---|
| `D02.ORL.LOCAL_ORAL` | 地域口承 | 地域住民間の口頭伝承。 |
| `D02.ORL.SCHOOL_ORAL` | 学校内伝承 | 学校・学級・生徒集団を中心とする口頭伝承。 |
| `D02.ORL.WORKPLACE_ORAL` | 職場内伝承 | 職場・職能集団内部の口頭伝承。 |
| `D02.ORL.FAMILY_ORAL` | 家族内伝承 | 家族・親族内で伝えられる口頭伝承。 |
| `D02.ORL.PEER_ORAL` | 友人・仲間内伝承 | 友人・同世代・趣味集団等の対人口承。 |

## 5.3. `D02.PRT` — 印刷・書簡

| Child ID | Child | 定義 |
|---|---|---|
| `D02.PRT.LETTER` | 手紙 | 個人間の書簡。 |
| `D02.PRT.CHAIN_LETTER` | チェーンレター | 複製・転送要求を含む連鎖書簡。 |
| `D02.PRT.NEWSPAPER` | 新聞 | 新聞記事・投書・新聞広告等。 |
| `D02.PRT.MAGAZINE` | 雑誌 | 一般誌・専門誌・ミニコミ等。 |
| `D02.PRT.BOOK` | 書籍 | 単行本・事典・怪談集等。 |
| `D02.PRT.LEAFLET` | チラシ・掲示物 | チラシ、掲示、配布文書等の短冊型印刷物。 |

## 5.4. `D02.BRD` — 放送

| Child ID | Child | 定義 |
|---|---|---|
| `D02.BRD.RADIO` | ラジオ | ラジオ番組・音声放送。 |
| `D02.BRD.TELEVISION` | テレビ | テレビ番組・ニュース・バラエティ等。 |

## 5.5. `D02.EDG` — 初期デジタル文字通信

| Child ID | Child | 定義 |
|---|---|---|
| `D02.EDG.PC_COMM` | パソコン通信 | 商用・草の根パソコン通信。 |
| `D02.EDG.BBS` | BBS・電子掲示板 | Web以前を含む電子掲示板・BBS。 |
| `D02.EDG.EMAIL` | Eメール | 電子メールによる個別・一斉転送。 |
| `D02.EDG.CHAT_EARLY` | チャット・IRC | 初期チャット、IRC等の同期文字通信。 |

## 5.6. `D02.WEB` — オープンWeb・ソーシャル

| Child ID | Child | 定義 |
|---|---|---|
| `D02.WEB.WEBSITE` | Webサイト | 独立Webサイト・ホームページ。 |
| `D02.WEB.BLOG` | ブログ・日記サービス | ブログ、Web日記、投稿日誌。 |
| `D02.WEB.FORUM` | Web掲示板・フォーラム | 2ch系を含む公開Web掲示板・フォーラム。 |
| `D02.WEB.SNS` | SNS | SNS投稿、短文投稿サービス。 |
| `D02.WEB.MESSAGING` | メッセージングアプリ | LINE等の閉鎖・半閉鎖型メッセージング。 |

## 5.7. `D02.AVD` — デジタル音声・映像

| Child ID | Child | 定義 |
|---|---|---|
| `D02.AVD.VIDEO_SITE` | 動画サイト | YouTube等のオンデマンド動画。 |
| `D02.AVD.LIVE_STREAM` | ライブ配信 | リアルタイム映像・音声配信。 |
| `D02.AVD.PODCAST` | Podcast・音声配信 | オンデマンド音声番組・Podcast。 |

## 5.8. `D02.INS` — 制度・記録媒体

| Child ID | Child | 定義 |
|---|---|---|
| `D02.INS.OFFICIAL_NOTICE` | 公的・公式告知 | 行政・企業・組織の公式告知。 |
| `D02.INS.REPORT_RECORD` | 報告書・記録 | 業務報告、研究報告、記録簿等。 |
| `D02.INS.LEGAL_MEDICAL_RECORD` | 法務・医療記録 | 裁判・警察・医療等の制度的記録。 |

---

# 6. D03. 確認流通媒体ポートフォリオ（Version Scope）

**型:** `H3`

**v2定義:** 「現在もっとも主要な媒体」を推測せず、指定Version Scopeで伝承が受容者へ流通したことを確認できる媒体をコードする。

Parent数: **7**

## 6.1. Primary / Secondary規則

1. Version Scopeの成立に構造的に不可欠な媒体
2. 資料が明示する主な拡散媒体
3. Version Scope内で最も早く直接確認できる媒体

残りの確認媒体をSecondary（0–2、順不同）とする。D02と同じ媒体でもよい。

## 6.2. 禁止事項

- 現在Web検索で見つかるだけで `Web` を付けない。
- 研究DB・ファクトチェック記事の存在だけでは流通媒体にしない。
- 複数候補からPrimaryを決められない場合は `C`。

## 6.3. `D03.ORL` — 口承・限定共同体

| Child ID | Child | 定義 |
|---|---|---|
| `D03.ORL.LOCAL_ORAL` | 地域口承 | 地域住民間の口頭伝承。 |
| `D03.ORL.SCHOOL_ORAL` | 学校内伝承 | 学校・学級・生徒集団を中心とする口頭伝承。 |
| `D03.ORL.WORKPLACE_ORAL` | 職場内伝承 | 職場・職能集団内部の口頭伝承。 |
| `D03.ORL.FAMILY_ORAL` | 家族内伝承 | 家族・親族内で伝えられる口頭伝承。 |
| `D03.ORL.PEER_ORAL` | 友人・仲間内伝承 | 友人・同世代・趣味集団等の対人口承。 |

## 6.4. `D03.PRT` — 印刷・書簡

| Child ID | Child | 定義 |
|---|---|---|
| `D03.PRT.LETTER` | 手紙 | 個人間の書簡。 |
| `D03.PRT.CHAIN_LETTER` | チェーンレター | 複製・転送要求を含む連鎖書簡。 |
| `D03.PRT.NEWSPAPER` | 新聞 | 新聞記事・投書・新聞広告等。 |
| `D03.PRT.MAGAZINE` | 雑誌 | 一般誌・専門誌・ミニコミ等。 |
| `D03.PRT.BOOK` | 書籍 | 単行本・事典・怪談集等。 |
| `D03.PRT.LEAFLET` | チラシ・掲示物 | チラシ、掲示、配布文書等の短冊型印刷物。 |

## 6.5. `D03.BRD` — 放送

| Child ID | Child | 定義 |
|---|---|---|
| `D03.BRD.RADIO` | ラジオ | ラジオ番組・音声放送。 |
| `D03.BRD.TELEVISION` | テレビ | テレビ番組・ニュース・バラエティ等。 |

## 6.6. `D03.EDG` — 初期デジタル文字通信

| Child ID | Child | 定義 |
|---|---|---|
| `D03.EDG.PC_COMM` | パソコン通信 | 商用・草の根パソコン通信。 |
| `D03.EDG.BBS` | BBS・電子掲示板 | Web以前を含む電子掲示板・BBS。 |
| `D03.EDG.EMAIL` | Eメール | 電子メールによる個別・一斉転送。 |
| `D03.EDG.CHAT_EARLY` | チャット・IRC | 初期チャット、IRC等の同期文字通信。 |

## 6.7. `D03.WEB` — オープンWeb・ソーシャル

| Child ID | Child | 定義 |
|---|---|---|
| `D03.WEB.WEBSITE` | Webサイト | 独立Webサイト・ホームページ。 |
| `D03.WEB.BLOG` | ブログ・日記サービス | ブログ、Web日記、投稿日誌。 |
| `D03.WEB.FORUM` | Web掲示板・フォーラム | 2ch系を含む公開Web掲示板・フォーラム。 |
| `D03.WEB.SNS` | SNS | SNS投稿、短文投稿サービス。 |
| `D03.WEB.MESSAGING` | メッセージングアプリ | LINE等の閉鎖・半閉鎖型メッセージング。 |

## 6.8. `D03.AVD` — デジタル音声・映像

| Child ID | Child | 定義 |
|---|---|---|
| `D03.AVD.VIDEO_SITE` | 動画サイト | YouTube等のオンデマンド動画。 |
| `D03.AVD.LIVE_STREAM` | ライブ配信 | リアルタイム映像・音声配信。 |
| `D03.AVD.PODCAST` | Podcast・音声配信 | オンデマンド音声番組・Podcast。 |

## 6.9. `D03.INS` — 制度・記録媒体

| Child ID | Child | 定義 |
|---|---|---|
| `D03.INS.OFFICIAL_NOTICE` | 公的・公式告知 | 行政・企業・組織の公式告知。 |
| `D03.INS.REPORT_RECORD` | 報告書・記録 | 業務報告、研究報告、記録簿等。 |
| `D03.INS.LEGAL_MEDICAL_RECORD` | 法務・医療記録 | 裁判・警察・医療等の制度的記録。 |

---

# 7. D04. 生成・変容パターン

**型:** `H3`

Parent数: **7**

## 7.1. `D04.STB` — 安定・固定

| Child ID | Child | 定義 |
|---|---|---|
| `D04.STB.SINGLE_FIXED` | 単発固定 | 確認範囲で構造変化が小さい。 |
| `D04.STB.STABILIZED_CANON` | 定型化・カノン化 | 多様な形から代表形が固定された。 |

## 7.2. `D04.VAR` — 再話・変異

| Child ID | Child | 定義 |
|---|---|---|
| `D04.VAR.ORAL_VARIATION` | 口承変異 | 口承過程で細部が変化する。 |
| `D04.VAR.RETELLING` | 再話 | 別の語り手・媒体で再叙述される。 |
| `D04.VAR.ACCRETION` | 増補 | 新ルール・新場面・新因果が追加される。 |
| `D04.VAR.LOCALIZATION` | 地域化 | 地名・施設・人物を地域に合わせて置換する。 |

## 7.3. `D04.MIG` — 媒体移行

| Child ID | Child | 定義 |
|---|---|---|
| `D04.MIG.MEDIUM_SHIFT` | 媒体移行 | 基本構造を保ち別媒体へ移る。 |
| `D04.MIG.DIGITAL_REAMPLIFICATION` | ネット再増幅 | 旧来伝承がネットで再流通・増幅する。 |
| `D04.MIG.FORMAT_TRANSLATION` | 形式変換 | 口承→ログ、手紙→メール等、提示形式も変わる。 |

## 7.4. `D04.COL` — 共同・分散生成

| Child ID | Child | 定義 |
|---|---|---|
| `D04.COL.LIVE_COCREATION` | 実況共同生成 | 参加者反応を取り込みながらリアルタイム生成される。 |
| `D04.COL.MULTI_AUTHOR` | 複数投稿者増殖 | 複数者が断片・異伝を追加する。 |
| `D04.COL.SERIALIZATION` | シリーズ化 | 同じ核から続編・連作が形成される。 |
| `D04.COL.DERIVATIVE_PROLIFERATION` | 派生増殖 | パロディ・亜種・派生ルールが多数生成される。 |

## 7.5. `D04.MED` — メディア展開

| Child ID | Child | 定義 |
|---|---|---|
| `D04.MED.MASS_ADAPTATION` | マスメディア化 | テレビ・映画・出版等で大規模再提示される。 |
| `D04.MED.COMMERCIALIZATION` | 商品・観光化 | 商品、イベント、観光資源等へ転用される。 |
| `D04.MED.CROSS_MEDIA` | クロスメディア化 | 複数メディア間で内容が相互変換される。 |

## 7.6. `D04.REC` — 再文脈化

| Child ID | Child | 定義 |
|---|---|---|
| `D04.REC.EVENT_ATTACHMENT` | 実事件への付着 | 実事件・事故・災害に後から結び付く。 |
| `D04.REC.PLACE_ATTACHMENT` | 場所への付着 | 特定地点へ後から伝説が固定される。 |
| `D04.REC.REVIVAL` | 再燃 | 一度衰退後、別時期に再流行する。 |
| `D04.REC.CONTEXT_UPDATE` | 時代適応 | 技術・制度・社会状況に合わせ内容を更新する。 |

## 7.7. `D04.CON` — 論争・起源変化

| Child ID | Child | 定義 |
|---|---|---|
| `D04.CON.DEBUNK_RECIRCULATION` | 反証を伴う再流通 | 否定・検証がかえって噂を再可視化する。 |
| `D04.CON.ORIGIN_LOSS` | 起源喪失 | 作者・初出が失われ伝承化する。 |
| `D04.CON.CONTESTED_VERSION` | 競合版併存 | 互いに異なる主要版が並行して維持される。 |
| `D04.CON.HOAX_REFRAMING` | 創作・冗談の伝説化 | 創作・冗談・虚構が真実らしい伝承へ再解釈される。 |

---

# 8. D05. 提示形式

**型:** `H3`

Parent数: **6**

## 8.1. `D05.EXP` — 体験叙述

| Child ID | Child | 定義 |
|---|---|---|
| `D05.EXP.RETROSPECTIVE_1P` | 一人称回想 | 体験者が後から一人称で回想する。 |
| `D05.EXP.LIVE_1P` | 一人称実況 | 進行中の体験を一人称で逐次報告する。 |
| `D05.EXP.CONFESSION_DIARY` | 告白・日記 | 告白、日記、私記として提示する。 |
| `D05.EXP.EXPERIENCE_SUMMARY` | 体験要約 | 個人経験を短く要約して提示する。 |

## 8.2. `D05.HRS` — 伝聞叙述

| Child ID | Child | 定義 |
|---|---|---|
| `D05.HRS.FOAF` | FOAF | 友人の友人等、近接伝聞として提示する。 |
| `D05.HRS.FAMILY_HEARSAY` | 家族伝聞 | 家族・親族から聞いた話として提示する。 |
| `D05.HRS.LOCAL_HEARSAY` | 地元伝聞 | 地元民・地域内部者の話として提示する。 |
| `D05.HRS.SCHOOL_WORK_HEARSAY` | 学校・職場伝承 | 学校・職場内部で共有される話として提示する。 |

## 8.3. `D05.DOC` — 記録・文書形式

| Child ID | Child | 定義 |
|---|---|---|
| `D05.DOC.LOG_THREAD` | ログ・スレッド | 掲示板・チャット等のログとして提示する。 |
| `D05.DOC.DIARY_REPORT` | 日誌・報告書 | 日誌・調査記録・報告書形式。 |
| `D05.DOC.NEWS_STYLE` | 新聞・ニュース風 | 報道・記事形式を取る。 |
| `D05.DOC.AV_RECORD` | 音声・映像記録 | 録音・動画・監視映像等の記録として提示する。 |

## 8.4. `D05.PRP` — 命題・主張形式

| Child ID | Child | 定義 |
|---|---|---|
| `D05.PRP.FACT_CLAIM` | 事実主張 | XはYである、という事実命題。 |
| `D05.PRP.EXPLANATORY_CLAIM` | 説明命題 | XはYが原因である、という説明命題。 |
| `D05.PRP.PREDICTIVE_CLAIM` | 予測命題 | XならYになる、という予測命題。 |
| `D05.PRP.CLASSIFICATION_CLAIM` | 類型命題 | A型はBの性質を持つ、という分類命題。 |

## 8.5. `D05.RUL` — 規則・警告形式

| Child ID | Child | 定義 |
|---|---|---|
| `D05.RUL.WARNING` | 警告 | 危険・禁止事項を警告する。 |
| `D05.RUL.TABOO` | 禁忌 | してはいけない行為を規定する。 |
| `D05.RUL.RITUAL_PROCEDURE` | 儀式・手順 | 特定の実践手順を提示する。 |
| `D05.RUL.CHAIN_INSTRUCTION` | 連鎖指示 | 転送・伝達等を要求する。 |
| `D05.RUL.JINX_RULE` | ジンクス規則 | 行為と吉凶・成功失敗を結ぶ規則。 |

## 8.6. `D05.HYB` — 集合・複合形式

| Child ID | Child | 定義 |
|---|---|---|
| `D05.HYB.COLLAB_THREAD` | 参加型実況 | 複数参加者の応答で成立する実況形式。 |
| `D05.HYB.MULTI_TESTIMONY` | 複数証言 | 複数人物の証言を束ねて提示する。 |
| `D05.HYB.QA_EXPERT` | Q&A・解説混合 | 質問回答・専門家説明を組み合わせる。 |
| `D05.HYB.NARRATIVE_EXPLANATION` | 物語＋解説 | 物語本文と由来・解説を組み合わせる。 |

---

# 9. D06. 真実性提示

**型:** `S`

| Value ID | 値 | 定義 |
|---|---|---|
| `D06.T1` | 直接体験事実 | 語り手自身の経験として真実性を主張する。 |
| `D06.T2` | 近接伝聞事実 | 友人・家族等の身近な人物からの伝聞として主張する。 |
| `D06.T3` | 共同体既知事実 | 地域・学校・職場等で既知のこととして提示する。 |
| `D06.T4` | 一般・制度・科学事実 | 一般事実、制度事実、科学的事実のように提示する。 |
| `D06.T5` | 条件付き信念 | 確実とは限らないが「XならYらしい」と信念・規則として提示する。 |
| `D06.T6` | 真偽未確定 | 不明・謎・噂として真偽を開いたまま提示する。 |
| `D06.T7` | 虚構・反証既知の再流通 | 虚構起源・否定・反証が知られつつ伝承として流通する。 |

---

# 10. D07. 意味形成対象

**型:** `H3`

Parent数: **9**

## 10.1. `D07.ANO` — 異常体験・存在

| Child ID | Child | 定義 |
|---|---|---|
| `D07.ANO.ANOMALOUS_PERCEPTION` | 異常知覚・体験 | 説明しにくい知覚・身体感覚・体験。 |
| `D07.ANO.UNKNOWN_EXISTENCE` | 未知存在 | 正体不明の存在・生物・怪異がいるのかという不確実性。 |
| `D07.ANO.UNEXPLAINED_EVENT` | 説明不能事象 | 原因不明の出来事・現象。 |
| `D07.ANO.DREAM_SLEEP_ANOMALY` | 夢・睡眠異常 | 夢、金縛り、睡眠中の不可解な経験。 |

## 10.2. `D07.DCF` — 死・偶然・不運

| Child ID | Child | 定義 |
|---|---|---|
| `D07.DCF.UNEXPLAINED_DEATH_LOSS` | 不可解な死・喪失 | 死、失踪、喪失の理由や意味。 |
| `D07.DCF.COINCIDENCE_PROBABILITY` | 偶然・確率 | 偶然の一致、低確率事象の意味。 |
| `D07.DCF.MISFORTUNE_STREAK` | 不運・成功失敗の偏り | 連敗、故障、事故等の偏り。 |
| `D07.DCF.FATE_OMEN` | 運命・予兆 | 将来の死・災厄・成功をどう予測するか。 |

## 10.3. `D07.PSE` — 場所・空間・環境

| Child ID | Child | 定義 |
|---|---|---|
| `D07.PSE.DANGEROUS_PLACE` | 危険・怪異場所 | なぜその場所が危険・不気味なのか。 |
| `D07.PSE.SPATIAL_ROUTE_ANOMALY` | 空間・経路異常 | 道、駅、距離、接続等の異常。 |
| `D07.PSE.HIDDEN_VANISHED_PLACE` | 隠れた・消えた場所 | 存在しない／消えた場所の説明。 |
| `D07.PSE.ENVIRONMENTAL_ANOMALY` | 環境異常 | 音、光、気温、自然環境等の不可解。 |

## 10.4. `D07.ICT` — 対人・犯罪脅威

| Child ID | Child | 定義 |
|---|---|---|
| `D07.ICT.STRANGER_THREAT` | 見知らぬ他者の脅威 | 都市空間の見知らぬ他者への不安。 |
| `D07.ICT.ABDUCTION_ASSAULT` | 誘拐・暴行 | 誘拐、性暴力、襲撃等の危険。 |
| `D07.ICT.HIDDEN_CRIMINAL_PRACTICE` | 隠れた犯罪慣行 | 臓器売買等、見えない犯罪実務。 |
| `D07.ICT.OUTGROUP_THREAT` | 外集団脅威 | 外国人・特定集団等への脅威認識。 |

## 10.5. `D07.BHF` — 身体・健康・食品

| Child ID | Child | 定義 |
|---|---|---|
| `D07.BHF.SYMPTOM_DISEASE` | 症状・疾病 | 症状、病気、感染等の原因やリスク。 |
| `D07.BHF.BODY_ANOMALY` | 身体異常 | 身体構造・生理の不可解や俗説。 |
| `D07.BHF.MEDICAL_RISK` | 医療リスク | 治療、医療行為、病院に関する不確実性。 |
| `D07.BHF.FOOD_CONTAMINATION` | 食品・摂取リスク | 食品、飲料、異物、汚染等の不安。 |
| `D07.BHF.SEX_REPRODUCTION` | 性・生殖 | 性行為、妊娠、生殖に関する不確実性。 |

## 10.6. `D07.TPS` — 技術・製品・システム

| Child ID | Child | 定義 |
|---|---|---|
| `D07.TPS.DEVICE_PRODUCT_FAILURE` | 機器・製品故障 | 製品がなぜ壊れる／異常動作するのか。 |
| `D07.TPS.HIDDEN_PRODUCT_FUNCTION` | 隠れた製品機能 | 意図的機能、タイマー、隠し仕様等。 |
| `D07.TPS.DIGITAL_SYSTEM_ANOMALY` | デジタル異常 | コンピュータ、ネットワーク、データの不可解。 |
| `D07.TPS.TECH_RISK_SURVEILLANCE` | 技術リスク・監視 | 電磁波、監視、技術的危険等。 |

## 10.7. `D07.INO` — 制度・組織

| Child ID | Child | 定義 |
|---|---|---|
| `D07.INO.HIDDEN_RULE_PROCEDURE` | 隠れた制度・手続 | 制度の見えない規則や抜け道。 |
| `D07.INO.ORGANIZATIONAL_SECRECY` | 組織秘密 | 企業・行政等の秘密・隠蔽。 |
| `D07.INO.INSTITUTIONAL_MANIPULATION` | 制度的操作 | 組織が人や結果を操作しているという不透明性。 |
| `D07.INO.OCCUPATIONAL_HIDDEN_PRACTICE` | 職業内部慣行 | 専門職・職場の隠れた実務・慣習。 |
| `D07.INO.SYSTEM_CAPACITY_FAILURE` | 制度能力への不安 | 制度が守れない、機能しないことへの不安。 |

## 10.8. `D07.ING` — 属性・規範・集団

| Child ID | Child | 定義 |
|---|---|---|
| `D07.ING.PERSONALITY_ATTRIBUTE` | 性格・属性差 | 人の性格や行動差を説明したい。 |
| `D07.ING.GROUP_STEREOTYPE` | 集団特性 | 血液型、地域、職業等の集団特徴。 |
| `D07.ING.NORM_MORALITY` | 規範・道徳 | なぜしてはいけない／すべきか。 |
| `D07.ING.BELONGING_BOUNDARY` | 所属・内外境界 | 誰が内部／外部なのか。 |

## 10.9. `D07.ISU` — 情報・社会的不確実性

| Child ID | Child | 定義 |
|---|---|---|
| `D07.ISU.INFORMATION_VOID` | 情報空白 | 情報不足・説明不在を埋める。 |
| `D07.ISU.CRISIS_SCARCITY` | 危機・不足 | 災害、品不足、社会危機への不確実性。 |
| `D07.ISU.PUBLIC_FIGURE_UNKNOWN` | 著名人・メディアの空白 | 著名人の生死、裏事情等の空白。 |
| `D07.ISU.FUTURE_SOCIAL_CHANGE` | 将来・社会変化 | 未来予測、社会変化への不安。 |

---

# 11. D08. 意味形成契機

**型:** `H3`

Parent数: **7**

## 11.1. `D08.DEX` — 直接経験

| Child ID | Child | 定義 |
|---|---|---|
| `D08.DEX.PERCEPTUAL_ANOMALY` | 知覚異常 | 見る・聞く等の異常知覚が契機。 |
| `D08.DEX.BODILY_SENSATION` | 身体感覚 | 痛み、麻痺、感覚異常等が契機。 |
| `D08.DEX.DIRECT_EVENT` | 出来事への直接遭遇 | 事故、故障、異常出来事への直接遭遇。 |
| `D08.DEX.DREAM_SLEEP_EVENT` | 夢・睡眠経験 | 夢、金縛り等の睡眠経験。 |

## 11.2. `D08.STY` — 社会的証言

| Child ID | Child | 定義 |
|---|---|---|
| `D08.STY.WITNESS_REPORT` | 目撃証言 | 他者の直接目撃証言。 |
| `D08.STY.FOAF_REPORT` | 近接伝聞 | 友人の友人等の伝聞。 |
| `D08.STY.COMMUNITY_REPETITION` | 共同体反復証言 | 地域・学校等で繰り返し聞く証言。 |
| `D08.STY.AUTHORITY_TESTIMONY` | 権威者証言 | 専門家、職員、権威ある人物の証言。 |

## 11.3. `D08.PAT` — パターン・相関

| Child ID | Child | 定義 |
|---|---|---|
| `D08.PAT.REPEATED_COINCIDENCE` | 反復する偶然 | 似た偶然が繰り返される。 |
| `D08.PAT.TEMPORAL_ASSOCIATION` | 時間的関連 | Xの後にYが起きる等の時間的相関。 |
| `D08.PAT.FREQUENCY_PATTERN` | 頻度・偏り | 多い／少ないという観察。 |
| `D08.PAT.SIMILARITY_ANALOGY` | 類似・対応 | 複数事例の似方を手掛かりにする。 |

## 11.4. `D08.TRC` — 記録・物的痕跡

| Child ID | Child | 定義 |
|---|---|---|
| `D08.TRC.PHOTO_VIDEO_AUDIO` | 写真・映像・音声 | 記録媒体の異常を証拠視する。 |
| `D08.TRC.TEXT_DOCUMENT` | 文書・記載 | 文書、メモ、記事、ログ等。 |
| `D08.TRC.PHYSICAL_TRACE` | 物的痕跡 | 物、傷、跡、遺留品等。 |
| `D08.TRC.MISSING_ALTERED_RECORD` | 欠落・改変記録 | 記録がない／消えた／書き換わったこと。 |

## 11.5. `D08.HIS` — 事件・歴史・場所痕跡

| Child ID | Child | 定義 |
|---|---|---|
| `D08.HIS.RECENT_INCIDENT` | 最近の事件・事故 | 比較的新しい事件・事故。 |
| `D08.HIS.HISTORICAL_EVENT` | 歴史事件・戦争・災害 | 戦争、災害、歴史事件。 |
| `D08.HIS.DEATH_CRIME_HISTORY` | 死亡・犯罪履歴 | 死亡、殺人、犯罪の履歴。 |
| `D08.HIS.PLACE_NAME_RUIN` | 地名・遺構・記念物 | 地名、遺構、塚、慰霊碑等。 |

## 11.6. `D08.OPA` — 技術・制度の不透明性

| Child ID | Child | 定義 |
|---|---|---|
| `D08.OPA.MALFUNCTION` | 故障・異常挙動 | 機器や制度の予期しない挙動。 |
| `D08.OPA.OPAQUE_RULE` | 不透明な規則・判断 | 制度ルールや決定理由が見えない。 |
| `D08.OPA.RESTRICTED_ACCESS` | 非公開・アクセス制限 | 立入禁止、秘密、非公開性。 |
| `D08.OPA.DATA_SYSTEM_GAP` | データ・システム空白 | データ不在、説明不能なシステム挙動。 |

## 11.7. `D08.CLM` — 命題先行

| Child ID | Child | 定義 |
|---|---|---|
| `D08.CLM.INHERITED_SAYING` | 既存の言い伝え | 「昔からそう言う」こと自体が出発点。 |
| `D08.CLM.UNSUPPORTED_ASSERTION` | 根拠未提示の主張 | 証拠を伴わない断定・噂。 |
| `D08.CLM.IMPORTED_MEDIA_CLAIM` | 外部媒体からの主張 | テレビ・本・ネット等の主張を手掛かりとして受容。 |
| `D08.CLM.FICTION_MEDIA_SEED` | 創作・冗談起源 | 創作、冗談、演出等が後に意味形成の種になる。 |

---

# 12. D09. 意味付与操作

**型:** `H3`

Parent数: **9**

## 12.1. `D09.CAT` — カテゴリー化

| Child ID | Child | 定義 |
|---|---|---|
| `D09.CAT.NAMING` | 命名 | 未知のものに名前を付ける。 |
| `D09.CAT.TYPE_ASSIGNMENT` | 類型化 | 既知カテゴリ・類型へ分類する。 |
| `D09.CAT.BOUNDARY_CLASSIFICATION` | 境界分類 | 安全／危険、内／外等の境界を作る。 |

## 12.2. `D09.CAU` — 原因帰属

| Child ID | Child | 定義 |
|---|---|---|
| `D09.CAU.DIRECT_CAUSE` | 直接原因化 | XがYを起こしたと結ぶ。 |
| `D09.CAU.HIDDEN_CAUSE` | 隠れた原因化 | 見えない原因を仮定する。 |
| `D09.CAU.BLAME_RESPONSIBILITY` | 責任帰属 | 人・組織・集団へ責任を割り当てる。 |

## 12.3. `D09.AGN` — 主体・意図帰属

| Child ID | Child | 定義 |
|---|---|---|
| `D09.AGN.AGENCY_ATTRIBUTION` | 主体化 | 現象に意思ある主体を置く。 |
| `D09.AGN.MOTIVE_ATTRIBUTION` | 動機付与 | 悪意、保護、復讐等の目的を付ける。 |
| `D09.AGN.COORDINATED_INTENT` | 協調意図・陰謀 | 複数主体の計画的意図を仮定する。 |

## 12.4. `D09.PPR` — パターン化・予測

| Child ID | Child | 定義 |
|---|---|---|
| `D09.PPR.CORRELATION_RULE` | 相関規則化 | XとYの対応を規則とみなす。 |
| `D09.PPR.OMEN_FORECAST` | 予兆・予測 | 現在の兆候から未来を予測する。 |
| `D09.PPR.RECURRENCE_RULE` | 反復規則 | 周期・再発・順序の規則を作る。 |
| `D09.PPR.ANALOGICAL_PATTERN` | 類推パターン | 似た事例から一般規則を作る。 |

## 12.5. `D09.NOR` — 価値・規範化

| Child ID | Child | 定義 |
|---|---|---|
| `D09.NOR.GOOD_BAD_VALUATION` | 吉凶・善悪評価 | 出来事や対象へ正負の価値を付ける。 |
| `D09.NOR.TABOOIZATION` | 禁忌化 | 特定行為を禁止すべきものにする。 |
| `D09.NOR.MORALIZATION` | 道徳化 | 報い・罰・徳等の道徳意味を付ける。 |
| `D09.NOR.PURITY_CONTAMINATION` | 穢れ・汚染化 | 清浄／不浄、汚染の枠組みで理解する。 |

## 12.6. `D09.CTL` — 制御規則形成

| Child ID | Child | 定義 |
|---|---|---|
| `D09.CTL.AVOIDANCE_RULE` | 回避規則 | 近づかない等の回避ルールを作る。 |
| `D09.CTL.RITUAL_RULE` | 儀式規則 | 実行手順・終了手順を作る。 |
| `D09.CTL.TRANSMISSION_RULE` | 伝達規則 | 転送・誰かに話す等の規則を作る。 |
| `D09.CTL.VERIFICATION_RULE` | 検証・訂正规則 | 確認、反証、公式情報照合等の規則を作る。 |

## 12.7. `D09.SSI` — 社会・制度解釈

| Child ID | Child | 定義 |
|---|---|---|
| `D09.SSI.SYSTEM_LOGIC` | 制度論理化 | 制度の仕組みとして説明する。 |
| `D09.SSI.HIDDEN_STRUCTURE` | 隠れた構造化 | 表面下の組織・制度構造を仮定する。 |
| `D09.SSI.GROUP_BOUNDARY` | 集団境界化 | 内集団／外集団の差として説明する。 |
| `D09.SSI.ROLE_RULE` | 役割規則化 | 職業・立場固有の規則として説明する。 |

## 12.8. `D09.HST` — 由来化・歴史化

| Child ID | Child | 定義 |
|---|---|---|
| `D09.HST.EVENT_ORIGIN` | 事件起源化 | 特定事件を起源として説明する。 |
| `D09.HST.HISTORICAL_ANCHOR` | 歴史接続 | 歴史人物・戦争・地域史へ接続する。 |
| `D09.HST.GENEALOGY_TRADITION` | 系譜・伝統化 | 家系・世代・伝統の連続として説明する。 |

## 12.9. `D09.UNK` — 不可知性保持

| Child ID | Child | 定義 |
|---|---|---|
| `D09.UNK.MYSTERY_LABEL` | 謎として命名 | 説明せず「謎」「怪異」としてラベル化する。 |
| `D09.UNK.DELIBERATE_NONRESOLUTION` | 非解決維持 | 複数説を残し結論を閉じない。 |
| `D09.UNK.FORBIDDEN_INQUIRY` | 知識境界化 | 調べてはいけない／知ってはいけないとする。 |

---

# 13. D10. 因果源存在論

**型:** `H3`

Parent数: **7**

## 13.1. `D10.HUM` — 人間・社会主体

| Child ID | Child | 定義 |
|---|---|---|
| `D10.HUM.INDIVIDUAL_HUMAN` | 個人 | 通常の個人が因果源。 |
| `D10.HUM.INFORMAL_GROUP` | 非制度的集団・共同体 | 村、家系、群衆、仲間集団等。 |
| `D10.HUM.ORGANIZATION` | 組織・制度主体 | 企業、国家、学校、病院等。 |
| `D10.HUM.COLLECTIVE_BEHAVIOR` | 集合行動 | 群衆・市場・社会全体の行動が因果源。 |

## 13.2. `D10.SUP` — 超自然主体・力

| Child ID | Child | 定義 |
|---|---|---|
| `D10.SUP.GHOST_SPIRIT` | 幽霊・死者霊 | 死者、亡霊、怨霊等。 |
| `D10.SUP.YOKAI_ENTITY` | 妖怪・人格怪異 | 妖怪、怪人、非人間人格主体。 |
| `D10.SUP.DEITY_DIVINE` | 神格・超越主体 | 神、神格的存在、超越的意思。 |
| `D10.SUP.IMPERSONAL_CURSE` | 非人格的呪力 | 人格主体を置かない呪い・祟りの力。 |

## 13.3. `D10.BIO` — 異常生物・内在存在

| Child ID | Child | 定義 |
|---|---|---|
| `D10.BIO.ANOMALOUS_ORGANISM` | 異常生物・UMA | 未知生物、巨大生物等。 |
| `D10.BIO.PARASITE_INTERNAL` | 寄生体・内在生物 | 身体内部に住む生物・存在。 |
| `D10.BIO.TRANSFORMED_HYBRID` | 変異・混成生物 | 人面、変身、混成体等。 |

## 13.4. `D10.OBJ` — 物体・情報・記号

| Child ID | Child | 定義 |
|---|---|---|
| `D10.OBJ.CURSED_OBJECT` | 呪物 | 異常作用を保持する物体。 |
| `D10.OBJ.ARTIFACT_DEVICE` | 人工物・機器 | 装置、製品、人工物自体。 |
| `D10.OBJ.INFORMATION_CONTENT` | 情報内容 | 文章、知識、噂、意味内容自体。 |
| `D10.OBJ.SYMBOL_NAME_IMAGE` | 記号・名称・図像 | 名前、数字、画像、記号等。 |

## 13.5. `D10.SPC` — 場所・時空

| Child ID | Child | 定義 |
|---|---|---|
| `D10.SPC.SPECIFIC_PLACE` | 特定場所 | 建物、道、山、池等の地点。 |
| `D10.SPC.ROUTE_CONNECTION` | 経路・接続 | 道、駅、路線、接続関係。 |
| `D10.SPC.ALTERNATE_WORLD` | 異界・別世界 | 通常世界とは異なる世界層。 |
| `D10.SPC.SPATIOTEMPORAL_FIELD` | 時空領域 | 場所・時間の場そのものが原因。 |

## 13.6. `D10.NAT` — 自然・生物物理過程

| Child ID | Child | 定義 |
|---|---|---|
| `D10.NAT.PHYSICAL_ENV_PROCESS` | 物理・環境過程 | 自然現象、物理作用、環境条件。 |
| `D10.NAT.BIOPHYSIO_PROCESS` | 生理・生物過程 | 睡眠、生理、遺伝等の自然過程。 |
| `D10.NAT.CHEM_PATHO_PROCESS` | 化学・病理過程 | 毒性、感染、病理等。 |
| `D10.NAT.PROBABILITY_PROCESS` | 確率・偶然過程 | 確率、偶然、統計的偏り。 |
| `D10.NAT.TECHNICAL_PROCESS` | 技術・システム過程 | 故障機構、アルゴリズム、非意図的システム作用。 |

## 13.7. `D10.PHN` — 現象・体験

| Child ID | Child | 定義 |
|---|---|---|
| `D10.PHN.ANOMALOUS_EXPERIENCE` | 異常体験 | 独立主体を仮定しない異常体験。 |
| `D10.PHN.DREAM_SLEEP_PHENOMENON` | 夢・睡眠現象 | 夢、金縛り等の現象そのもの。 |
| `D10.PHN.UNEXPLAINED_PHYSICAL_PHENOMENON` | 未説明物理現象 | 物音、物体移動等で原因主体を確定しない。 |
| `D10.PHN.SYNCHRONICITY_OMEN` | 符合・予兆現象 | 虫の知らせ、意味ある偶然等。 |

---

# 14. D11. 発動・接触条件

**型:** `H3`

Parent数: **8**

## 14.1. `D11.SEN` — 感覚曝露

| Child ID | Child | 定義 |
|---|---|---|
| `D11.SEN.VISUAL_EXPOSURE` | 見る | 視覚的に対象へ曝露する。 |
| `D11.SEN.AUDITORY_EXPOSURE` | 聞く | 声・音を聞く。 |
| `D11.SEN.TACTILE_EXPOSURE` | 触る | 接触・触知する。 |
| `D11.SEN.OTHER_SENSORY` | 嗅ぐ・味わう等 | 嗅覚・味覚等の曝露。 |

## 14.2. `D11.INF` — 情報曝露

| Child ID | Child | 定義 |
|---|---|---|
| `D11.INF.READ_VIEW_MEDIA` | 読む・媒体を見る | 文書・画像・映像等の内容へ接触する。 |
| `D11.INF.LEARN_KNOW` | 知る | 情報・名称・事実を知る。 |
| `D11.INF.SAY_NAME_REMEMBER` | 言う・名前を唱える・記憶する | 発話・記憶が条件になる。 |
| `D11.INF.UNDERSTAND_RECOGNIZE` | 理解・認識する | 意味を理解・認識することが条件。 |
| `D11.INF.RECEIVE_MESSAGE` | 通知・メッセージを受ける | メール、電話、通知等を受信する。 |

## 14.3. `D11.MAN` — 操作・儀式

| Child ID | Child | 定義 |
|---|---|---|
| `D11.MAN.OPEN_UNSEAL` | 開ける・封を解く | 箱、扉、封印等を開く。 |
| `D11.MAN.TAKE_OWN_CARRY` | 持つ・所有・持ち帰る | 対象を取得・所持する。 |
| `D11.MAN.CREATE_ALTER_MANIPULATE` | 作る・加工・操作する | 対象を作る、壊す、加工する。 |
| `D11.MAN.PHOTO_RECORD` | 撮影・記録する | 写真・録音・映像化する。 |
| `D11.MAN.PERFORM_RITUAL` | 儀式・唱和を行う | 手順、召喚、唱和等を実行する。 |
| `D11.MAN.RESPOND_CHOOSE` | 答える・選択する | 質問への回答や選択を行う。 |

## 14.4. `D11.MOV` — 移動・空間進入

| Child ID | Child | 定義 |
|---|---|---|
| `D11.MOV.ENTER_PASS_CROSS` | 入る・通る・越える | 場所・境界へ進入する。 |
| `D11.MOV.RIDE_BOARD` | 乗る | 車両・船等に乗る。 |
| `D11.MOV.EXIT_ALIGHT` | 降りる・出る | 車両・場所から降りる／出る。 |
| `D11.MOV.FOLLOW_TURN_ROUTE` | 曲がる・逆回り・経路選択 | 特定方向・順序で移動する。 |

## 14.5. `D11.SOC` — 社会関係・取引

| Child ID | Child | 定義 |
|---|---|---|
| `D11.SOC.MEET_INTERACT` | 会う・会話する | 人物・集団と直接交流する。 |
| `D11.SOC.RELATION_FAMILY` | 家族・恋愛関係になる | 血縁・婚姻・親密関係が条件。 |
| `D11.SOC.WORK_EMPLOYMENT` | 働く・雇われる | 職務・雇用関係に入る。 |
| `D11.SOC.CONTRACT_EXCHANGE` | 契約・購入・交換 | 取引・交換・購入を行う。 |
| `D11.SOC.INVESTIGATE_INQUIRE` | 調査・問い合わせ | 探索、質問、調査を行う。 |

## 14.6. `D11.CON` — 時刻・属性・状態条件

| Child ID | Child | 定義 |
|---|---|---|
| `D11.CON.TIME_DATE` | 特定時刻・日付 | 時刻、曜日、日付等。 |
| `D11.CON.AGE_LIFESTAGE` | 年齢・ライフステージ | 年齢、学年、妊娠等。 |
| `D11.CON.PERSONAL_ATTRIBUTE` | 個人属性 | 血液型、名前、性別等の属性。 |
| `D11.CON.LOCATION_STATE` | 位置・状態条件 | 特定場所にいる、特定状態にある。 |

## 14.7. `D11.PAS` — 受動発生

| Child ID | Child | 定義 |
|---|---|---|
| `D11.PAS.SLEEP_DREAM` | 眠る・夢を見る | 睡眠状態になること。 |
| `D11.PAS.SYMPTOM_ILLNESS` | 発症する | 症状・病気が自然に起きる。 |
| `D11.PAS.ACCIDENT_INVOLVEMENT` | 事故・出来事に巻き込まれる | 非意図的に出来事へ巻き込まれる。 |
| `D11.PAS.SPONTANEOUS_SELECTION` | 偶然選ばれる・遭遇する | 本人の選択なく対象となる。 |

## 14.8. `D11.NCR` — 接触不要

| Child ID | Child | 定義 |
|---|---|---|
| `D11.NCR.INTRINSIC_PROPERTY` | 内在属性のみ | 属性を持つだけで成立する。 |
| `D11.NCR.AMBIENT_EFFECT` | 環境・社会に広く作用 | 個別接触を必要としない。 |

---

# 15. D12. 作用対象

**型:** `H3`

Parent数: **8**

## 15.1. `D12.FOC` — 焦点人物

| Child ID | Child | 定義 |
|---|---|---|
| `D12.FOC.PROTAGONIST_EXPERIENCER` | 主人公・体験者 | 物語・体験の焦点人物。 |
| `D12.FOC.PRACTITIONER` | 実践者 | 儀式・行為を実行した人物。 |

## 15.2. `D12.OTH` — 他者個人

| Child ID | Child | 定義 |
|---|---|---|
| `D12.OTH.SPECIFIC_OTHER` | 特定他者 | 主人公以外の特定人物。 |
| `D12.OTH.BYSTANDER_WITNESS` | 傍観者・目撃者 | 居合わせた人物・目撃者。 |
| `D12.OTH.VICTIM_TARGET` | 特定被害者 | 被害対象として選ばれた人物。 |

## 15.3. `D12.KIN` — 親密者・血縁

| Child ID | Child | 定義 |
|---|---|---|
| `D12.KIN.FAMILY_BLOODLINE` | 家族・血縁 | 家族、親族、家系。 |
| `D12.KIN.PARTNER_FRIEND` | 恋人・友人 | 親密な非血縁者。 |

## 15.4. `D12.GRP` — 集団・共同体

| Child ID | Child | 定義 |
|---|---|---|
| `D12.GRP.SMALL_GROUP` | 小集団 | クラス、チーム、乗客等の限定集団。 |
| `D12.GRP.LOCAL_COMMUNITY` | 地域共同体 | 村、地域住民等。 |
| `D12.GRP.DEMOGRAPHIC_GROUP` | 属性集団 | 特定年代、性別、民族等。 |
| `D12.GRP.UNSPECIFIED_PEOPLE` | 不特定人群 | 特定されない複数の人々。 |

## 15.5. `D12.ORG` — 組織・制度

| Child ID | Child | 定義 |
|---|---|---|
| `D12.ORG.ORGANIZATION` | 組織 | 企業、学校、病院等の組織。 |
| `D12.ORG.INSTITUTION_SYSTEM` | 制度・社会システム | 制度、規則、市場等。 |

## 15.6. `D12.OTD` — 物体・技術・データ

| Child ID | Child | 定義 |
|---|---|---|
| `D12.OTD.OBJECT_PRODUCT` | 物体・商品 | 物、商品、所有物。 |
| `D12.OTD.DEVICE_INFRA` | 機器・インフラ | 機械、車両、設備、インフラ。 |
| `D12.OTD.DATA_RECORD` | データ・記録 | ファイル、記録、文書データ。 |

## 15.7. `D12.ENV` — 場所・環境・世界

| Child ID | Child | 定義 |
|---|---|---|
| `D12.ENV.PLACE_BUILDING` | 場所・建物 | 地点、建築物、施設。 |
| `D12.ENV.NATURAL_ENVIRONMENT` | 自然環境 | 山、海、森林等。 |
| `D12.ENV.SPATIAL_WORLD_STATE` | 空間・世界状態 | 経路、空間、世界の状態。 |

## 15.8. `D12.AUD` — 受容者・公衆

| Child ID | Child | 定義 |
|---|---|---|
| `D12.AUD.NARRATOR_TELLER` | 語り手 | 伝承を語る／投稿する人物。 |
| `D12.AUD.READER_LISTENER` | 読者・聞き手 | 伝承を受容した人物。 |
| `D12.AUD.NEXT_RECIPIENT` | 次の受信者 | 転送・伝達先の人物。 |
| `D12.AUD.GENERAL_PUBLIC` | 一般公衆 | 社会一般の人々。 |

---

# 16. D13. 作用機構

**型:** `H3`

**設計メモ:** MANIFEST_ONLYは作用情報が欠けている場合には使用しない。Uと区別する。

Parent数: **9**

## 16.1. `D13.MAN` — 顕現・観測

| Child ID | Child | 定義 |
|---|---|---|
| `D13.MAN.MANIFEST_ONLY` | 顕現のみ | 現れる／認識されるが追加作用を必須としない。 |

## 16.2. `D13.PHY` — 身体・物質作用

| Child ID | Child | 定義 |
|---|---|---|
| `D13.PHY.PHYSICAL_ATTACK` | 物理攻撃 | 通常物理的に身体を損傷する。 |
| `D13.PHY.PHYSIOLOGICAL_CHANGE` | 生理変化 | 病気、麻痺、身体機能等を変える。 |
| `D13.PHY.BODY_TRANSFORMATION` | 身体変容 | 形態・外見・身体構造を変える。 |
| `D13.PHY.BODY_INTRUSION` | 身体侵入 | 異物・存在が身体内部へ侵入する。 |
| `D13.PHY.ENV_OBJECT_MANIPULATION` | 環境・物体操作 | 物体移動、機器異常、環境変化を起こす。 |

## 16.3. `D13.REL` — 追跡・対象関係操作

| Child ID | Child | 定義 |
|---|---|---|
| `D13.REL.PURSUIT` | 追跡 | 対象との距離を縮め追う。 |
| `D13.REL.TARGETING` | 標的化 | 特定対象を選び固定する。 |
| `D13.REL.LURING` | 誘引 | 危険な場所・状態へ近づける。 |
| `D13.REL.MIMICRY` | 擬態 | 既知人物・声・物へ似せて欺く。 |
| `D13.REL.PERSISTENT_ATTACHMENT` | 付着・再出現 | 接触後も関係が切れず再出現する。 |
| `D13.REL.OTHER_ANOMALY_INTERFERENCE` | 他怪異干渉 | 別の怪異を排除・捕食・操作する。 |

## 16.4. `D13.INT` — 内在・支配

| Child ID | Child | 定義 |
|---|---|---|
| `D13.INT.POSSESSION_CONTROL` | 憑依・支配 | 身体・精神へ入り制御する。 |
| `D13.INT.PARASITIC_HABITATION` | 寄生 | 宿主内部に定着し資源を利用する。 |
| `D13.INT.SYMBIOTIC_DEPENDENCE` | 共生・依存 | 宿主との相互依存関係を形成する。 |

## 16.5. `D13.COG` — 認知・情報作用

| Child ID | Child | 定義 |
|---|---|---|
| `D13.COG.COGNITION_TRIGGERED_HARM` | 認知災害 | 知る・見る・理解すること自体が作用条件。 |
| `D13.COG.MENTAL_INFLUENCE` | 精神干渉 | 恐怖、幻覚、強迫等を直接誘発する。 |
| `D13.COG.MEMORY_ALTERATION` | 記憶改変・欠落 | 記憶を消去・変更する。 |
| `D13.COG.INFORMATION_INDUCED_ACTION` | 情報誘導・行動誘発 | 信念・判断を変え通常行動を介して結果を起こす。 |

## 16.6. `D13.RST` — 現実・時空作用

| Child ID | Child | 定義 |
|---|---|---|
| `D13.RST.REALITY_ALTERATION` | 現実改変 | 同一世界の客観状態を書き換える。 |
| `D13.RST.REALITY_REPLACEMENT` | 現実置換 | 別の現実・世界状態へ移す。 |
| `D13.RST.SPATIAL_DISTORTION` | 空間異常 | 距離・接続・地理を崩す。 |
| `D13.RST.TEMPORAL_DISTORTION` | 時間異常 | 時間進行・順序・同期を崩す。 |

## 16.7. `D13.TRN` — 伝播

| Child ID | Child | 定義 |
|---|---|---|
| `D13.TRN.PERSON_TRANSFER` | 人から人への伝播 | 異常条件が次の人へ移る。 |
| `D13.TRN.MEDIA_OBJECT_TRANSFER` | 媒体・物体媒介伝播 | 物、手紙、媒体等を介して移る。 |
| `D13.TRN.HEREDITARY_TRANSFER` | 血縁・世代伝播 | 家系・世代を通じて継承される。 |

## 16.8. `D13.SOC` — 社会・制度作用

| Child ID | Child | 定義 |
|---|---|---|
| `D13.SOC.CONCEAL_SUPPRESS` | 隠蔽・抑圧 | 情報・事件を隠す、口止めする。 |
| `D13.SOC.EXCLUDE_STIGMATIZE` | 排除・烙印 | 差別、排除、信用剥奪を起こす。 |
| `D13.SOC.COERCE_CONFINE` | 強制・監禁 | 制度・集団が行動を強制・拘束する。 |
| `D13.SOC.INSTITUTIONAL_MANIPULATION` | 制度操作 | 制度・市場・組織手続を利用して結果を動かす。 |

## 16.9. `D13.FAT` — 運命・吉凶作用

| Child ID | Child | 定義 |
|---|---|---|
| `D13.FAT.CURSE_MISFORTUNE` | 呪詛・不運付与 | 非物理的に病気、不運、事故等を付与する。 |
| `D13.FAT.FATE_FIXING` | 運命固定 | 将来結果を変更困難にする。 |
| `D13.FAT.LUCK_BENEFIT` | 幸運・利益付与 | 幸運、成功、利益を付与する。 |

---

# 17. D14. 帰結極性

**型:** `S`

| Value ID | 値 | 定義 |
|---|---|---|
| `D14.NEG` | 負 | 最終帰結が主として損失・危害。 |
| `D14.NEU` | 中立 | 正負いずれとも言い難い、観測・説明のみ。 |
| `D14.POS` | 正 | 最終帰結が主として利益・成功・保護。 |
| `D14.MIX` | 混合 | 重要な正負帰結が併存する。 |

---

# 18. D15. 帰結領域

**型:** `H3`

Parent数: **9**

## 18.1. `D15.BOD` — 身体・健康

| Child ID | Child | 定義 |
|---|---|---|
| `D15.BOD.DISCOMFORT_MINOR` | 不快・軽症 | 一時的不快、軽傷等。 |
| `D15.BOD.DISEASE_ILLNESS` | 病気・感染 | 疾病、感染、慢性症状。 |
| `D15.BOD.SEVERE_INJURY` | 重傷・障害 | 重傷、身体欠損、後遺障害。 |
| `D15.BOD.DEATH` | 死亡 | 死亡・致死。 |
| `D15.BOD.BODY_CHANGE_CONTAMINATION` | 身体変化・汚染 | 変容、異物化、汚染。 |

## 18.2. `D15.MND` — 精神・認知

| Child ID | Child | 定義 |
|---|---|---|
| `D15.MND.FEAR_TRAUMA` | 恐怖・トラウマ | 恐怖、不安、トラウマ。 |
| `D15.MND.SLEEP_DISTURBANCE` | 睡眠障害 | 不眠、悪夢、睡眠障害。 |
| `D15.MND.PERCEPTUAL_DISTURBANCE` | 知覚異常 | 幻覚、異常知覚。 |
| `D15.MND.MEMORY_COGNITION` | 記憶・認知障害 | 記憶喪失、混乱等。 |
| `D15.MND.COMPULSION_BEHAVIOR` | 強迫・衝動 | 強迫、異常衝動。 |
| `D15.MND.SELF_IDENTITY_DISRUPTION` | 自我・同一性崩壊 | 自我、人格、自己認識の崩壊。 |

## 18.3. `D15.SOC` — 社会関係・地位

| Child ID | Child | 定義 |
|---|---|---|
| `D15.SOC.RELATION_BREAKDOWN` | 関係破綻 | 恋愛、家族、友人関係の悪化。 |
| `D15.SOC.REPUTATION_TRUST` | 信用・評判 | 評判、信用の低下／向上。 |
| `D15.SOC.EXCLUSION_STIGMA` | 排除・烙印 | 社会的孤立、差別。 |
| `D15.SOC.JOB_SCHOOL_STATUS` | 職業・学業地位 | 失職、退学、昇進・合格等。 |
| `D15.SOC.LEGAL_CRIMINAL_STATUS` | 法的・犯罪者地位 | 逮捕、犯罪者扱い等。 |

## 18.4. `D15.MAT` — 物的・技術的・経済的

| Child ID | Child | 定義 |
|---|---|---|
| `D15.MAT.PROPERTY_DAMAGE` | 財産・物損 | 物品・財産の損壊。 |
| `D15.MAT.MONEY_GAIN_LOSS` | 金銭損益 | 金銭・売上・費用の増減。 |
| `D15.MAT.DEVICE_DATA_LOSS` | 機器・データ損失 | 機器故障、データ削除。 |
| `D15.MAT.RESOURCE_SCARCITY` | 物資不足 | 買い占め、欠品、資源不足。 |
| `D15.MAT.INFRA_DISRUPTION` | インフラ障害 | 交通、通信等の機能障害。 |

## 18.5. `D15.BEH` — 行動・選択

| Child ID | Child | 定義 |
|---|---|---|
| `D15.BEH.AVOIDANCE_ROUTE_CHANGE` | 回避・経路変更 | 場所や行動を避ける。 |
| `D15.BEH.RITUAL_COMPULSIVE_ACTION` | 儀式・反復行動 | 儀式、強迫的行為を行う。 |
| `D15.BEH.PURCHASE_HOARDING` | 購入・買い占め | 購買、備蓄、買い占め。 |
| `D15.BEH.SHARING_TRANSMISSION` | 伝達・拡散 | 噂・情報を他者へ伝える。 |
| `D15.BEH.RISKY_HARMFUL_ACTION` | 危険行動 | 危険・有害な行為を選ぶ。 |
| `D15.BEH.COMPLIANCE_DECISION` | 遵守・意思決定変化 | 制度・規則・助言に従う／選択を変える。 |

## 18.6. `D15.LIF` — 人生・存在・同一性

| Child ID | Child | 定義 |
|---|---|---|
| `D15.LIF.FUTURE_CONSTRAINT` | 将来制約 | 将来の選択肢・運命が狭まる。 |
| `D15.LIF.DISAPPEARANCE` | 失踪・消失 | 行方不明、存在消失。 |
| `D15.LIF.LIFE_SUCCESS_FAILURE` | 人生上の成否 | 結婚、出世、長期成功失敗。 |
| `D15.LIF.IDENTITY_TRANSFORMATION` | 同一性変化 | 人格・身分・存在状態の変化。 |
| `D15.LIF.EXISTENCE_ERASURE` | 存在履歴消去 | 記録・存在の抹消。 |

## 18.7. `D15.KNW` — 世界認識・知識

| Child ID | Child | 定義 |
|---|---|---|
| `D15.KNW.UNCERTAINTY_PRESERVED` | 不確実性維持 | 謎・不明のまま残る。 |
| `D15.KNW.BELIEF_REVISION` | 信念変更 | 世界観・解釈が変わる。 |
| `D15.KNW.REVELATION_KNOWLEDGE` | 真相・知識獲得 | 新たな説明・情報を得る。 |
| `D15.KNW.REALITY_TRUST_LOSS` | 現実信頼喪失 | 現実・記録への信頼が崩れる。 |

## 18.8. `D15.COL` — 集団・社会・制度

| Child ID | Child | 定義 |
|---|---|---|
| `D15.COL.PANIC` | 集団パニック | 広範な不安・混乱。 |
| `D15.COL.COLLECTIVE_VIOLENCE` | 集団暴力・差別 | 差別、暴力、迫害。 |
| `D15.COL.INSTITUTIONAL_LOAD_POLICY` | 制度負荷・政策影響 | 行政・組織対応、制度変更。 |
| `D15.COL.MARKET_SOCIAL_BEHAVIOR` | 市場・社会行動変化 | 市場、交通、消費等の集団行動。 |
| `D15.COL.COMMUNITY_CHANGE` | 共同体変化 | 地域慣習・関係構造の変化。 |

## 18.9. `D15.OPP` — 吉凶・機会

| Child ID | Child | 定義 |
|---|---|---|
| `D15.OPP.LUCK_MISFORTUNE` | 幸運・不運 | 一般的な運の上下。 |
| `D15.OPP.ROMANCE` | 恋愛成否 | 恋愛、縁結び、破局。 |
| `D15.OPP.EXAM_CAREER` | 試験・職業成否 | 合格、就職、昇進等。 |
| `D15.OPP.WISH_FULFILLMENT` | 願望成就 | 願いが叶う／叶わない。 |
| `D15.OPP.DISASTER_AVOIDANCE` | 災厄回避 | 災害・事故等を避ける。 |

---

# 19. D16. 因果時間構造

**型:** `H3`

**v2定義:** 発動条件・原因成立から主作用／主帰結までの時間的編成をコードする。伝承自体の流行期間ではない。

Parent数: **7**

- 時間順序を持たない属性・対応・規則は `STA`。
- 一続きの出来事内で完結し長い遅延が意味上重要でない場合は `EVT`。
- 明示的遅延・期限・潜伏は `DLY`。
- 徐々に進展は `PRG`。
- 一度収束後の再発は `REC`。
- 切れ目ない持続は `CON`。
- 対象間・世代間を移る場合は `TRN`。
- `U` は動的時間構造が重要なのに資料から決められない場合に限定する。

## 19.1. `D16.STA` — 無時間的・静的関係

| Child ID | Child | 定義 |
|---|---|---|
| `D16.STA.STATIC_ATTRIBUTE` | 静的属性・同一性 | 「XはYである」等、時間進行を必要としない属性・同一性主張。 |
| `D16.STA.STATIC_ASSOCIATION` | 静的対応・相関 | 「XならY」「場所Xでは現象Y」等、時間順序を主題としない対応関係。 |
| `D16.STA.STATIC_RULE` | 静的規則 | 制度・俗信等の条件規則で、待ち時間・進行過程が重要でない。 |
| `D16.STA.ENDURING_CONDITION` | 持続状態 | 場所・対象が恒常的に異常状態にあるという主張。 |

## 19.2. `D16.EVT` — 単一エピソード・事象内

| Child ID | Child | 定義 |
|---|---|---|
| `D16.EVT.IMMEDIATE` | 即時 | 接触直後に作用・結果が起きること自体が重要。 |
| `D16.EVT.SINGLE_OBSERVATION` | 単発観測 | 一度の出現・経験で完結する。 |
| `D16.EVT.SINGLE_EPISODE` | 単一エピソード | 一続きの出来事内で作用・結果が完結する。 |
| `D16.EVT.SEQUENTIAL_EPISODE` | エピソード内段階進行 | 一つの出来事内で複数段階が順に起きる。 |

## 19.3. `D16.DLY` — 遅延・期限・潜伏

| Child ID | Child | 定義 |
|---|---|---|
| `D16.DLY.DELAYED` | 遅延 | 一定時間後に発現する。 |
| `D16.DLY.DEADLINE` | 期限付き | 特定期限までに行動／結果が生じる。 |
| `D16.DLY.LATENT` | 潜伏 | 潜伏期間後に発現する。 |

## 19.4. `D16.PRG` — 進行・長期

| Child ID | Child | 定義 |
|---|---|---|
| `D16.PRG.STAGED_PROGRESSION` | 段階進行 | 複数段階を経て中長期に進展する。 |
| `D16.PRG.GRADUAL_EROSION` | 長期浸食 | 徐々に生活・精神等を侵食する。 |
| `D16.PRG.LIFELONG` | 生涯 | 生涯にわたり作用する。 |

## 19.5. `D16.REC` — 再発・周期

| Child ID | Child | 定義 |
|---|---|---|
| `D16.REC.RECURRENT` | 再発 | 一度収束後、不定期に再び起こる。 |
| `D16.REC.PERIODIC` | 周期 | 毎年、毎夜等の周期で起きる。 |
| `D16.REC.TRIGGERED_RECURRENCE` | 条件再発 | 同じ条件成立のたび再発する。 |

## 19.6. `D16.CON` — 持続・追跡

| Child ID | Child | 定義 |
|---|---|---|
| `D16.CON.CONTINUOUS` | 連続持続 | 作用が切れ目なく継続する。 |
| `D16.CON.PURSUIT_DURATION` | 追跡継続 | 追跡関係として持続する。 |
| `D16.CON.PERSISTENT_ATTACHMENT` | 付着持続 | 対象との関係が切れず続く。 |

## 19.7. `D16.TRN` — 連鎖・世代

| Child ID | Child | 定義 |
|---|---|---|
| `D16.TRN.CHAIN_SPREAD` | 連鎖拡散 | A→B→Cと対象間を移る。 |
| `D16.TRN.SUCCESSIVE_VICTIMS` | 順次対象化 | 順番に複数対象へ作用する。 |
| `D16.TRN.INTERGENERATIONAL` | 世代継承 | 家系・世代を越えて続く。 |

## 19.8. v1からの移行

- `D16.IMS.IMMEDIATE` → `D16.EVT.IMMEDIATE`
- `D16.IMS.SINGLE_OBSERVATION` → `D16.EVT.SINGLE_OBSERVATION`
- 旧Uの命題・属性型は `STA`、一つの出来事内で完結する物語は `EVT` を検討する。

---

# 20. D17. 回避・制御方式

**型:** `H3`

Parent数: **8**

## 20.1. `D17.AVO` — 回避・逃走

| Child ID | Child | 定義 |
|---|---|---|
| `D17.AVO.DO_NOT_ENGAGE` | 接触回避 | 見ない、入らない、触らない等。 |
| `D17.AVO.FLEE_ESCAPE` | 逃走 | 追跡・危険から物理的に逃げる。 |
| `D17.AVO.DISTANCE_ROUTE_CHANGE` | 距離・経路変更 | 場所・経路を変える。 |

## 20.2. `D17.RUL` — 規則遵守

| Child ID | Child | 定義 |
|---|---|---|
| `D17.RUL.OBEY_TABOO` | 禁忌遵守 | 禁止事項を守る。 |
| `D17.RUL.CORRECT_ANSWER` | 正答・選択 | 正しい答えや選択肢を選ぶ。 |
| `D17.RUL.TIMING_ORDER` | 時刻・順序遵守 | 指定時間・順番を守る。 |
| `D17.RUL.PROCEDURAL_RULE` | 手順遵守 | 決められた操作手順を守る。 |

## 20.3. `D17.RIT` — 儀式・専門介入

| Child ID | Child | 定義 |
|---|---|---|
| `D17.RIT.RITUAL_CLOSURE` | 儀式終了・祓い | 儀式、供養、祓い等。 |
| `D17.RIT.RELIGIOUS_SPECIALIST` | 宗教専門家 | 僧侶、神職、霊能者等。 |
| `D17.RIT.MEDICAL_PROFESSIONAL` | 医療介入 | 医師・医療的対応。 |
| `D17.RIT.LEGAL_OFFICIAL` | 公的・法的介入 | 警察、行政、法制度等。 |

## 20.4. `D17.CST` — 代償・転嫁・管理

| Child ID | Child | 定義 |
|---|---|---|
| `D17.CST.PAYMENT_SACRIFICE` | 代償・犠牲 | 金銭、供物、犠牲を支払う。 |
| `D17.CST.TRANSFER_SUBSTITUTE` | 転嫁・身代わり | 別人・別物へ移す。 |
| `D17.CST.CONTAINMENT` | 封印・隔離 | 対象を封じ込める。 |
| `D17.CST.ONGOING_MANAGEMENT` | 継続管理 | 完全除去せず管理・共存する。 |

## 20.5. `D17.INF` — 情報・技術的制御

| Child ID | Child | 定義 |
|---|---|---|
| `D17.INF.VERIFY_DEBUNK` | 検証・反証 | 公式情報や証拠で真偽確認する。 |
| `D17.INF.DO_NOT_FORWARD_CORRECT` | 不拡散・訂正 | 転送しない、訂正を共有する。 |
| `D17.INF.TECHNICAL_RESTORE` | 技術復旧 | バックアップ、修復、設定復旧等。 |
| `D17.INF.SAFETY_EVIDENCE_ACTION` | 安全・科学的対応 | 安全手順、根拠ある予防策を取る。 |

## 20.6. `D17.USE` — 利用・活用

| Child ID | Child | 定義 |
|---|---|---|
| `D17.USE.DELIBERATE_INVOCATION` | 意図的利用 | 怪異・規則を意図的に呼び出す。 |
| `D17.USE.LUCK_EXPLOITATION` | 吉兆利用 | 幸運・願掛けとして利用する。 |
| `D17.USE.STRATEGIC_RULE_USE` | 規則の戦略利用 | ルールを利用し利益を得る。 |

## 20.7. `D17.UNA` — 不可避

| Child ID | Child | 定義 |
|---|---|---|
| `D17.UNA.NO_KNOWN_ESCAPE` | 回避法なし | 知られた回避法がない。 |
| `D17.UNA.FIXED_OUTCOME` | 固定結果 | 条件成立後は結果が変更不能。 |

## 20.8. `D17.NON` — 制御不要

| Child ID | Child | 定義 |
|---|---|---|
| `D17.NON.OBSERVATIONAL_ONLY` | 観測のみ | 危害・不利益がなく介入不要。 |
| `D17.NON.BENIGN_NO_CONTROL` | 無害・自然消失 | 無害または自然に終わり制御不要。 |

---

# 21. D18. 作用レイヤー

**型:** `B`

独立binary bit。複数を同時に1にできる。

| Bit ID | レイヤー | 定義 |
|---|---|---|
| `D18.L1` | 伝承内因果層 | 伝承内容内部で人物・物体・環境等に因果作用がある。 |
| `D18.L2` | 受容者層 | 読む・聞く・受信する現実側の受容者が伝承内容上の因果対象になる。 |
| `D18.L3` | 社会現実層 | 噂の流通により現実社会で確認可能な行動・制度・市場等の結果が生じる。 |

---

# 22. D19. 流通範囲

**型:** `H3`

Parent数: **7**

## 22.1. `D19.PRI` — 個人・極小範囲

| Child ID | Child | 定義 |
|---|---|---|
| `D19.PRI.ISOLATED_EXPERIENCER` | 単独経験者 | ほぼ単一人物・単一証言に限定。 |
| `D19.PRI.PRIVATE_HOUSEHOLD` | 私的世帯 | 家庭・極小私的範囲。 |

## 22.2. `D19.KIN` — 家族・仲間

| Child ID | Child | 定義 |
|---|---|---|
| `D19.KIN.FAMILY_NETWORK` | 家族・親族 | 家族・親族ネットワーク。 |
| `D19.KIN.FRIEND_PEER` | 友人・同輩 | 友人、同世代、仲間集団。 |
| `D19.KIN.SCHOOL_YOUTH` | 学校・若者集団 | 学校・生徒・学生文化。 |

## 22.3. `D19.LOC` — 地域共同体

| Child ID | Child | 定義 |
|---|---|---|
| `D19.LOC.NEIGHBORHOOD` | 近隣・町内 | 近隣、町内、特定施設周辺。 |
| `D19.LOC.REGIONAL` | 地域・地方 | 市町村・地方圏等。 |
| `D19.LOC.LOCAL_TRADITION` | 地域伝承圏 | 祭礼・郷土伝承を含む地域文化圏。 |

## 22.4. `D19.PRO` — 職業・専門コミュニティ

| Child ID | Child | 定義 |
|---|---|---|
| `D19.PRO.OCCUPATIONAL` | 職業集団 | 同業者・職場横断の職業集団。 |
| `D19.PRO.EXPERT_SPECIALIST` | 専門家集団 | 医療、研究、技術等の専門家。 |
| `D19.PRO.HOBBY_SUBCULTURE` | 趣味・サブカル集団 | ファン、趣味、専門コミュニティ。 |

## 22.5. `D19.ORG` — 組織内部

| Child ID | Child | 定義 |
|---|---|---|
| `D19.ORG.COMPANY_INSTITUTION` | 企業・組織内部 | 企業、学校、病院等の内部。 |
| `D19.ORG.STATE_MILITARY` | 国家・軍・行政内部 | 国家機関、軍、行政等。 |
| `D19.ORG.RELIGIOUS_CLOSED_GROUP` | 宗教・閉鎖集団 | 宗教組織、閉鎖的団体等。 |

## 22.6. `D19.NET` — ネットワーク公開圏

| Child ID | Child | 定義 |
|---|---|---|
| `D19.NET.CLOSED_ONLINE` | 閉鎖オンライン | 限定チャット、会員制掲示板等。 |
| `D19.NET.OPEN_FORUM_WEB` | 公開Web・掲示板 | 公開掲示板、Webサイト。 |
| `D19.NET.SNS_VIRAL` | SNS・拡散ネットワーク | SNSによる広域拡散。 |

## 22.7. `D19.MAS` — 大衆・広域社会

| Child ID | Child | 定義 |
|---|---|---|
| `D19.MAS.NATIONAL_PUBLIC` | 全国的大衆 | 全国規模の一般社会。 |
| `D19.MAS.CROSS_GENERATIONAL` | 世代横断的大衆 | 複数世代に広く共有。 |
| `D19.MAS.TRANSNATIONAL` | 国際・越境流通 | 複数国・言語圏にまたがる。 |

---

# 23. D20. 特権情報保持者

**型:** `H3`

Parent数: **7**

## 23.1. `D20.NON` — 特権なし

| Child ID | Child | 定義 |
|---|---|---|
| `D20.NON.COMMON_KNOWLEDGE` | 一般共有 | 特定保持者なく広く共有。 |
| `D20.NON.NO_HIDDEN_TRUTH` | 隠れた真相なし | 追加の秘密情報を想定しない。 |

## 23.2. `D20.PER` — 当事者・家族

| Child ID | Child | 定義 |
|---|---|---|
| `D20.PER.EXPERIENCER` | 体験者本人 | 本人だけが追加情報を持つ。 |
| `D20.PER.FAMILY_BLOODLINE` | 家族・家系 | 家族・血縁だけが知る。 |

## 23.3. `D20.INS` — 地元・内部者

| Child ID | Child | 定義 |
|---|---|---|
| `D20.INS.LOCAL_RESIDENT` | 地元住民 | 地域内部者だけが知る。 |
| `D20.INS.SCHOOL_WORK_INSIDER` | 学校・職場内部者 | 学校・職場の内部者。 |
| `D20.INS.SUBCULTURE_VETERAN` | 古参・サブカル内部者 | 特定コミュニティの古参等。 |

## 23.4. `D20.EXP` — 専門家・職能者

| Child ID | Child | 定義 |
|---|---|---|
| `D20.EXP.MEDICAL_SCIENTIFIC` | 医療・科学専門家 | 医師、研究者等。 |
| `D20.EXP.TECHNICAL_OCCUPATIONAL` | 技術・職業専門家 | 技術者、職人、乗務員等。 |
| `D20.EXP.RELIGIOUS_FOLKLORE` | 宗教・伝承専門家 | 僧侶、神職、霊能者、伝承知識者等。 |

## 23.5. `D20.ORG` — 組織・加害主体

| Child ID | Child | 定義 |
|---|---|---|
| `D20.ORG.INSTITUTION_AUTHORITY` | 組織・権限主体 | 企業、行政、学校等の権限主体。 |
| `D20.ORG.PERPETRATOR_CRIMINAL` | 加害者・犯罪者 | 加害者側だけが知る。 |
| `D20.ORG.SECRET_NETWORK` | 秘密組織・ネットワーク | 陰謀主体、秘密結社等。 |

## 23.6. `D20.UNK` — 到達不能・不明

| Child ID | Child | 定義 |
|---|---|---|
| `D20.UNK.NO_ONE_KNOWS` | 誰も知らない | 伝承内でも真相保持者が存在しない。 |
| `D20.UNK.LOST_ORIGIN` | 失われた情報 | かつての情報が失われている。 |
| `D20.UNK.DEAD_MISSING_HOLDER` | 死亡・失踪保持者 | 保持者が死亡・失踪しアクセス不能。 |

## 23.7. `D20.HAZ` — 危険・禁制情報

| Child ID | Child | 定義 |
|---|---|---|
| `D20.HAZ.DANGEROUS_TO_KNOW` | 知ること自体が危険 | 情報へのアクセス自体が危害条件。 |
| `D20.HAZ.TABOO_RESTRICTED` | 禁忌・閲覧制限 | 知識が禁忌・禁止される。 |
| `D20.HAZ.CURSED_RECORD` | 呪われた記録 | 文書・記録自体が危険。 |

---

# 24. D21. 現実アンカー

**型:** `O`

| Value ID | 値 | 定義 |
|---|---|---|
| `D21.A0` | 匿名・抽象 | 特定可能な実在対象へほぼ依存しない。 |
| `D21.A1` | 一般的現実背景 | 学校、病院、工場等の一般的背景。 |
| `D21.A2` | 具体的実在対象 | 特定地点・企業・商品・人物等を明示する。 |
| `D21.A3` | 実在制度・社会史が成立条件 | 制度、組織、事件史等がモデル成立に必要。 |
| `D21.A4` | 史実・記録・既存伝承を因果統合 | 具体的史実・記録・既存伝承を因果構造へ組み込む。 |

---

# 25. Parent/Child対応表の実装規則

実装ではChild→Parent対応を独立したマスターテーブルとして保持する。

```text
dimension_id | child_id | child_label | parent_id | parent_label | active_version
D13 | D13.PHY.PHYSICAL_ATTACK | 物理攻撃 | D13.PHY | 身体・物質作用 | v1
```

ExcelのParent列はXLOOKUP等、Pythonでは辞書lookupで自動生成する。手入力は禁止する。

# 26. H3保存規則

```text
D13_primary_child
D13_primary_parent       # derived
D13_secondary1_child
D13_secondary1_parent    # derived
D13_secondary2_child
D13_secondary2_parent    # derived
D13_status
```

Secondaryは順不同であり、`secondary1/2`は保存位置にすぎない。入力後にchild ID昇順でcanonicalizeする。

# 27. 情報量・粒度のパイロット判定規則

各H1/H3次元について、まずParentレベル、次にChildレベルを評価する。

- Parent primary: `K_declared`, `K_observed`, `H`, `H_norm`, `K_eff`, rare-code率。
- Child primary: Parent内部の詳細情報量として評価し、Parent entropyへ加算しない。
- Secondary: primary prevalence / secondary prevalence / any-position prevalence / pairwise co-occurrenceを評価。
- `K_eff/K_declared`が低い、rare childが多い、coder agreementが低い場合はChild統合またはParent再設計。
- 逆に1つのParent内でChild分布が安定し、研究上意味ある差を持つならChildを維持する。

# 28. 次工程

このv1は**理論先行taxonomy**であり、確定版ではない。次工程は、各Blockから層化抽出した40–60 Entryによるパイロット再コードである。

パイロットでは、コード不足・境界競合・Parent偏り・Child希少化・U/NA率・coder agreementを記録し、v2 code taxonomyへ更新する。

# 29. 方法論上の位置づけ

階層コードブックは、広いParentの下により具体的なChildを置き、定義・include/exclude・例をパイロットで反復修正する運用と整合する。Parent/Childは理論上の多次元化ではなく、同一概念を異なる粒度で記録するための実装である。

参考方法論:

- DeCuir-Gunby et al. (2011), codebook development and operational definitions.
- Krippendorff, Content Analysis, unitizing and coding reliability.
- Wickham (2014), Tidy Data: one variable per column, one observation per row.
- Team-based hierarchical codebook studies using parent/child code structures and iterative refinement.
# 30. 事前リスクフラグ

Parent数は全H1/H3次元で4–9の範囲に収まっている。ただしChild数は次元間で大きく異なる。

特にパイロットで重点監査する次元:

| 次元 | Child数 | 事前リスク |
|---|---:|---|
| D15 帰結領域 | 46 | rare Childの多発、隣接帰結の境界競合 |
| D07 意味形成対象 | 38 | 「何を説明するか」の抽象度差、複数対象の主副判定 |
| D11 発動・接触条件 | 34 | 具体動作Childの過分割、儀式と情報曝露の複合 |
| D13 作用機構 | 33 | 旧Mコードとの境界、機構と帰結の混同 |
| D09 意味付与操作 | 31 | 原因帰属・主体帰属・制度解釈の近接 |
| D02/D03 媒体 | 28 | 古い媒体の希少Child、初期媒体の典拠不足 |
| D10 因果源存在論 | 28 | 超自然主体・現象・場所の境界 |

**D13.MANの単一Childについて**


`D13.MAN`（顕現・観測）は現時点でChildが`MANIFEST_ONLY` 1つだけであり、階層としては冗長である。
しかし、Parentレベルで「追加作用なし」を他作用familyと比較する必要があるため、v1では保持する。

パイロット後に次のどちらかを選ぶ。

1. 実データで意味ある下位型が現れればChildを追加する。
2. 下位型が不要なら、実装上のみParent=Childの退化階層として維持するか、D13の特殊flat branchとして簡略化する。

無理にChildを増やして情報量を水増ししない。

# 31. v1確定時点の検証結果

- 21概念次元すべてに値体系を定義済み。
- H1/H3はすべてParent数4–9。
- 各Childは同一次元内で1つのParentにのみ所属する。
- H3はPrimary exactly 1 / Secondary 0–2を前提とする。
- ParentはChildからのderived fieldであり、独立入力しない。
- U / NA / Cはコード値ではなくstatusで管理する。
- Childの総数が多い次元は確定扱いせず、パイロットで統合・分割を判定する。
