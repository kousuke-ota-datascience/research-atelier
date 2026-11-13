# INV-000041 — Coverage matrix (supporting audit)

> Canonical authority: `00_context.json` → `10_evidence.json` → `20_synthesis.json` → `30_analysis.json`. This is a **descriptive evidence coverage map**, not a statistical census of all deployed industry use cases. A filled cell means **a captured study or example exists**; it does **not** mean routine production deployment or a particular achieved operational benefit.

## 1. Sector × analytical problem

| Sector | 現在の異常・イベント検知 | 変化点検知 | 故障・状態診断 | 将来の警告・イベント予測 | RUL／サイクル寿命 |
| --- | --- | --- | --- | --- | --- |
| 製造（加工・工程・半導体） | K0001, K0002, K0020 | K0018 | K0001 | K0001, K0020 | 未同定 |
| 鉄道（車両・分岐器） | K0031 | 未同定 | K0010（故障部位） | K0010（APU、2時間は**要件**） | 未同定 |
| 風力発電 | K0011（軸受） | 未同定 | K0005は**事後故障履歴** | K0012（突発停止） | 未同定 |
| 電力系統 | K0016（PMUイベント） | K0017（開閉操作） | 未同定 | 未同定 | 未同定 |
| 建築・HVAC | K0003（FDDの検出段階） | 未同定 | K0003 | 未同定 | 未同定 |
| IT・通信 | K0006, K0021（サービス／通信KPI） | 未同定 | 未同定 | 未同定 | 未同定 |
| 石油・ガス | K0022, K0023, K0030 | 未同定 | K0022, K0030 | K0024は予兆／保全判断の著者報告 | K0024（ESP、数量的精度未同定） |
| 水処理・配水・食品設備 | K0004, K0029 | 未同定 | K0025（既存漏水） | K0029（センサ値の将来予測であり故障確率ではない） | 未同定 |
| 航空機 | K0027（健全性監視） | 未同定 | K0027（故障アラート） | K0027（到着前整備の警告） | K0008（合成RUL） |
| 蓄電池 | 未同定 | 未同定 | 未同定 | 未同定 | K0014（実験室サイクル寿命） |
| 医療 | K0007（事後ECG分類、境界） | 未同定 | K0007（不整脈判読） | K0013（敗血症発症前の課題） | 未同定 |

## 2. Important boundary cases
- K0005: NREL wind-turbine gearbox event-history database supports post hoc failure classification, **not** sensor-time-series deployed anomaly detection.
- K0019: semiconductor failure occurrence/timing based on pre-shipment and maintenance history; **not necessarily online time-series sensor modeling**.
- K0015: operational disk failure data establish important limits of using SMART values alone for prediction, not a deployed effective predictor.
- K0026: finance AML fraud/anomalous account detection with transaction records, **temporal dependency modeling unverified**.
- K0028: earthquake **detection and incoming-shaking warning**, not earthquakes predicted before initiation and not equipment failure prognosis.
- K0007: ECG four-class recognition is a measured signal classification task, **not** future onset prediction.
- K0008: N-CMAPSS simulator uses real flight operating conditions but synthetic damage trajectories.

## 3. Operational quality / evidence-level semantics
Recorded classes include: (A) research-defined benchmark or controlled fault injection; (B) genuine field/operational data evaluated retrospectively; (C) reported field trials and prototypes; (D) vendor/operator-reported operational systems; (E) program goals or event-only historical data. These classes are **different evidence types, not a validated ordinal score**.

Prediction target, prediction horizon, **required versus achieved lead time**, output unit (score, class, probability, time-to-event), failure-event definition, censoring, intervention effects, and evaluation design must be inspected separately.

## 4. Open coverage gaps
- Across industry prognostics, well-documented **calibrated fixed-horizon failure probabilities** and censoring-aware event validation remain insufficiently established by the current captured Evidence.
- Actual deployment outcomes and causal maintenance benefits are seldom independently evaluated.
- Only selected industries, studies, and dates were screened. Lack of an example in this matrix means **not established in this sample**, not absence of all published work.
- A formal PRISMA-ScR-style review requires reproducible search retrieval, deduplication, explicit eligibility flow/counts, citation-chaining and fuller original-text verification; `search_audit.md` is a purposefully scoped search audit, not such a complete review.
