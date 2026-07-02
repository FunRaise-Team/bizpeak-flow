# 外部研究：CLM 產品地景 × 台灣電子簽章法 × B2B 收款催收自動化

**用途**：BizPeak Flow 功能規格對標
**日期**：2026-07-02
**研究範圍**：見文末 Task boundary

---

## 一、2026 CLM（Contract Lifecycle Management）產品地景

### 1.1 市場概況

CLM 是 2026 年最活躍的 SaaS 垂直領域之一，前十大廠商合計 ARR 超過 10 億美元。三個對標產品定位分明：

| 產品 | 定位 | 定價 | 導入時間 | 原生電子簽名 |
|------|------|------|----------|--------------|
| **Ironclad** | 中大型企業 / 有內部法務團隊 / 月合約量 100+ | 企業級（未公開，通常六位數美元/年） | 12 週以上 | 無，需外接 DocuSign / Adobe Sign |
| **DocuSign CLM** | 已用 DocuSign eSignature、想往上加流程管理 | 2萬〜10萬美元+/年 | 12 週以上 | 原生（signs in-product） |
| **PandaDoc** | 中小企業 / 業務團隊自助 | 19〜89 美元/使用者/月 | 1〜2 週 | 原生 |

**對 BizPeak Flow 的啟示**：三層定價/複雜度光譜（企業級重流程 vs 中小企業輕量自助）值得對照 BizPeak Flow 自己要卡在哪一層——若目標是台灣中小型 B2B，PandaDoc 的「1-2 週上線、per-user 定價、drag-and-drop 範本」路線比 Ironclad 更值得抄。

Sources: [ctacquisitions.com](https://ctacquisitions.com/best-clm-software-and-loi-tools-for-ma/), [vaquill.ai](https://www.vaquill.ai/blog/clm-ironclad-docusign-contractworks), [juro.com](https://juro.com/learn/docusign-clm-vs-ironclad-comparison), [aline.co](https://www.aline.co/post/ironclad-vs-docusign)

### 1.2 核心功能模組拆解（以 Ironclad 為例、模組化程度最高）

1. **Workflow Designer（流程設計器）**：拖拉式無程式碼介面，把既有合約範本（Word 檔上傳）包裝成可設條件式核准與路由規則的工作流程。業界公認是這個類別中最強的視覺化工作流程建構器。
2. **Clause Library（條款庫）**：全域條款庫可跨多個工作流程共用/編輯條款，而不是條款被綁死在單一流程設定裡。單一文件最多可標記 3,500 個條款變體、單一條款標籤可含最多 100 個條件式變體。
3. **Repository + AI 資料萃取**：集中式合約儲存、AI 自動萃取關鍵資料欄位、智慧標籤、全文檢索；Smart Import 可批次匯入舊有紙本/PDF 合約建檔。
4. **Version Control + Audit Trail**：版本控制與稽核軌跡是標配，不是加值功能。
5. **E-signature 整合**（非原生）：透過 DocuSign / Adobe Sign 完成簽署動作，本身不做簽名。
6. **AI Assist（合約審閱）**：Ironclad AI Assist（GPT-4 起）自動化合約審閱，屬於 AI-first 陣營（同陣營還有 Evisort、LinkSquares、Spotdraft）。
7. **Analytics Dashboard**：194+ 個合約 metadata 欄位、生命週期追蹤、使用量數據，續約管理訊號是其中較成熟的一塊。

**對 BizPeak Flow 的啟示**：
- 模組切法可直接借用：**範本/工作流程設計 → 條款/內容庫 → 儲存庫+搜尋 → 簽署（可外接不必自建）→ AI 審閱/摘要（差異化機會）→ Analytics（續約/到期提醒）**。
- 「簽署本身」不是 CLM 的核心護城河（Ironclad 自己都外包給 DocuSign），BizPeak Flow 若要做電子簽核，重點應放在「流程 + 資料萃取 + 分析」而非重造簽名輪子——可考慮直接串點點簽 DottedSign 之類的 API 而非自建簽章引擎。

Sources: [ironcladapp.com](https://ironcladapp.com/journal/contract-management/contract-lifecycle-management), [support.ironcladapp.com (Workflow Library)](https://support.ironcladapp.com/hc/en-us/articles/12271079600023-Workflow-Library-Overview), [support.ironcladapp.com (Clauses)](https://support.ironcladapp.com/hc/en-us/articles/30659495044759-Use-Clauses-in-Workflow-Designer)

### 1.3 台灣本地對標：點點簽 DottedSign

- 專業版方案：無上限簽署文件數、文件稽核軌跡（audit trail）、數位憑證 + OTP 雙重身分驗證、進階簽署欄位（印章/核取方塊/日期/圖片/超連結）、可設定範本、支援跨裝置（iOS/Android/Web）。
- 明確標榜符合台灣《電子簽章法》第 6 條：以數位簽章簽署電子文件，符合規定即推定為本人親自簽名或蓋章。
- 安全機制：TLS/SSL + AES-256 + RSA-2048 加密、整合中華電信憑證 CA。
- 應用場景明確列出「報價單、委任契約」——與 BizPeak Flow 的 B2B 報價/合約場景高度重疊。
- 提供 API 方案（凱鈿行動科技，也上架台灣雲市集 tcloud.gov.tw）。

**對 BizPeak Flow 的啟示**：DottedSign 是本地既有玩家、有政府雲市集背書、API 方案存在——若 BizPeak Flow 不自建簽章引擎，DottedSign API 是可行的整合對象；若要自建，至少要對標它的「OTP + 數位憑證雙軌」身分驗證設計與稽核軌跡欄位。

Sources: [dottedsign.com](https://www.dottedsign.com/features/digital-certificate-cht/), [explore.dottedsign.com](https://explore.dottedsign.com/taiwan-electronic-signature-act), [tcloud.gov.tw](https://tcloud.gov.tw/solution/F03FE16033570DAEE0531512620AC1A1)

---

## 二、台灣《電子簽章法》2024 修法後的法律效力與實務要件

### 2.1 修法背景

2024 年 4 月 30 日立法院三讀通過修正草案，是自 2001 年立法以來首次實質修法。現行主管機關為**數位發展部**（原經濟部）。權威來源：[全國法規資料庫](https://law.moj.gov.tw/LawClass/LawAll.aspx?pcode=J0080037)、[數位發展部主管法規共用系統](https://law.moda.gov.tw/LawContent.aspx?id=FL011349)。

### 2.2 三個概念的法律位階（由弱到強）

| 類型 | 定義 | 法律效力 | 舉證責任 |
|------|------|----------|----------|
| **電子簽名**（非法律用語） | 手寫板簽名、滑鼠軌跡模擬簽名等 | 無明文規範、無法鑑定筆跡，實務上效力最弱 | 主張方需自行舉證真實性 |
| **電子簽章**（法律用語） | 依附電子文件、用以辨識簽署人身分/確認文件真偽的電子方式 | 符合《電子簽章法》規定條件下，效力**等同於**實體文件及簽章 | 沒有「推定本人簽署」的效果 |
| **數位簽章**（電子簽章的子集） | 以數學演算法/私密金鑰加密、公開金鑰驗證、且由**憑證機構（CA）**簽發憑證 | 《電子簽章法》第 6 條：**推定為本人親自簽名或蓋章** | 舉證責任反轉——對造要證明「不是本人所為」 |

**修法核心變化**：
1. 明定電子文件/電子簽章法律效力**等同**實體文件，不得僅因電子形式否認其效力（參酌 UN、美、韓、歐盟立法例）。
2. 刪除「行政機關得公告排除本法適用」的規定，若有特殊原因最多只能展延一次、以兩年為限——大幅限縮政府機關拒收電子文件的空間。
3. 主管機關明確化為數位發展部。

Sources: [legalsign.ai](https://legalsign.ai/article/143), [lawbank.com.tw](https://www.lawbank.com.tw/news/NewsContent.aspx?NID=202153.00), [is-law.com](https://www.is-law.com/impact-and-expectations-of-the-amendments-to-the-electronic-signatures-act/), [legis-pedia.com](https://www.legis-pedia.com/article/lawABC/1499)

### 2.3 對 BizPeak Flow「內部簽核 vs 對客戶簽署」的實務啟示

- **對外（B2B 報價單/合約，對客戶）**：建議至少做到「電子簽章」等級（有身分辨識機制），有能力最好上「數位簽章」（綁 CA 憑證），因為對外文件一旦爭議進入訴訟，舉證責任反轉（推定本人簽署）是關鍵優勢。這也是點點簽把「報價單、委任契約」明確列為數位簽章應用場景的原因。
- **對內（企業內部簽核，如採購簽呈、請假單）**：法律風險等級低很多，「電子簽章」甚至「電子簽名」等級通常已足夠——業界慣例是內部同意書/流程確認用較輕量的驗證機制，不必每筆都上數位憑證，主要考量是使用便利性與內部治理，而非訴訟舉證力。
- **實務要件共通項**（不分內外）：身分驗證機制（OTP/簡訊/Email 驗證碼是常見基礎款）、完整稽核軌跡（誰在何時簽署、IP、裝置）、文件簽署後不可竄改（hash 比對）、若走數位簽章需綁定合格 CA（如中華電信、TWCA）。
- **對 BizPeak Flow 規格啟示**：功能規格應該把「簽署強度」設計成**可配置的分級**（電子簽名 for 內部低風險流程 → 電子簽章 for 一般內部簽核 → 數位簽章 for 對客戶的正式合約/報價單），而非單一簽署機制打天下；同時規格書要明確寫「稽核軌跡」是所有簽署動作的強制欄位，不是加值功能。

Sources: [dottedsign.com 電子/數位簽章比較](https://www.dottedsign.com/zh-tw/blog/product/electronic-and-digital-signature-comparison), [legis-pedia.com](https://www.legis-pedia.com/article/lawABC/1499), [ailegal.lawsnote.com](https://ailegal.lawsnote.com/blog/electronic-signature/)

---

## 三、B2B 收款催收自動化（Invoice → Payment Tracking → Dunning）業界標準流程

### 3.1 整體實施順序（不要一次做全套）

業界建議分階段導入、不要一次做完四塊，避免「做太快、上線就壞」：

**Invoicing（開立發票，消除延遲）→ Dunning（催收提醒自動化）→ Cash Application（收款自動勾稽）→ Reporting & Intelligence（報表與分析）**

其中前兩塊（開票 + 催收）對 DSO（應收帳款週轉天數）的改善效果最大、改動成本最低——多數 B2B SaaS 公司導入 90 天內可看到 DSO 下降 20-40%，最大效益來自消除開票延遲（原本常拖 1-3 天）與自動化催收序列。

Source: [ledgerup.ai](https://www.ledgerup.ai/accounts-receivable-automation)

### 3.2 標準 Dunning（催收）階段設計

業界典型的五到七階段模型：

| 階段 | 時間點 | 動作 | 語氣 |
|------|--------|------|------|
| 到期前提醒 | Day -3 | 主動提醒即將到期 | 友善 |
| 到期日通知 | Day 0 | 到期通知 | 中性 |
| 第一次逾期提醒 | Day +1~7 | 溫和提醒 | 友善 |
| 第二次跟催 | Day +7~14 | 較堅定的跟進 | 較堅定 |
| 正式催告 | Day +21~30 | 書面正式通知 | 正式 |
| 最終警告 | Day +45~60 | 最後通牒，說明後續程序 | 嚴正 |
| 轉催收/法務 | Day +60~90 | 移交第三方催收或法務程序 | 外部化 |

**關鍵原則**：
- 不能只用單一管道（Email），應多管道並行（簡訊、電話、Email），且序列要能依客戶行為分流——首次逾期客戶 vs 長期優質客戶 vs 慣性拖延客戶，催收力道應該不同，一體適用的催收序列會傷害好客戶關係、又對付不了真正的拖延者。
- **轉催收的臨界點**：多數信用政策把「多次聯繫未回應」+ 逾期 60-90 天設為轉外部催收/法務的門檻。逾期 90 天以上，回收機率降到約 50%；逾期 120 天以上，降到約 25%——這是催收自動化必須「盡早介入」的量化理由。
- **Dunning 與 Collections 的分野**：Dunning 是企業自己直接對客戶做的提醒流程；Collections 是內部催收失敗後、正式委外催收機構或走法律程序的階段。Dunning 在前、Collections 是 exit condition。

Sources: [creditpulse.com](https://www.creditpulse.com/blog/dunning-process-guide), [straive.com（7 階段框架）](https://www.straive.com/blogs/automated-dunning-that-doesnt-damage-relationships-a-7-stage-sequence-framework/), [legalclarity.org](https://legalclarity.org/dunning-process-stages-rules-and-best-practices/), [ledgerup.ai](https://www.ledgerup.ai/accounts-receivable-automation)

### 3.3 平台應具備的核心能力

自動化開票與催收工作流程、客戶自助繳費入口（self-service payment portal）、AI 驅動的收款勾稽（cash application）、即時分析報表、ERP 整合、可自訂的風險分級與催收規則。

Source: [montopay.com](https://montopay.com/accounts-receivable-automation-complete-guide-to-boosting-collection-rates/)

**對 BizPeak Flow 的啟示**：
- 催收模組不該是單一序列，規格上要支援「依客戶分群套用不同催收節奏」的規則引擎（例如 VIP 客戶 vs 高風險客戶）。
- 60-90 天是硬性的規格分水嶺——系統應該在這個時間點強制觸發「升級決策」（是否轉正式催告/停止服務/委外），而不是讓催收序列無限期軟性提醒下去。
- 若 BizPeak Flow 目標客群是台灣中小 B2B，多管道（簡訊在台灣接受度高）+ 客戶自助繳費入口，會比純 Email 序列更有效。

---

## 四、對 BizPeak Flow 規格的直接啟示（總結）

1. **模組切法**：範本/工作流程設計 → 條款/內容庫 → 儲存庫+搜尋 → 簽署（建議外接 API 不自建）→ AI 審閱/摘要（差異化機會點）→ Analytics（到期/續約提醒）。
2. **簽署強度分級**：內部簽核可用較輕量的電子簽章/電子簽名，對客戶的報價單/合約建議上數位簽章（綁 CA），因為訴訟舉證責任反轉是硬優勢；稽核軌跡是所有簽署動作的強制欄位。
3. **簽章技術路線**：優先評估串接點點簽 DottedSign API（本地既有、有政府雲市集背書、支援 OTP+數位憑證），而非自建簽章引擎——連 Ironclad 都外接 DocuSign/Adobe Sign。
4. **催收模組**：規則引擎需支援依客戶分群套用不同催收節奏；60-90 天設為強制升級決策點；建議多管道（簡訊+Email）+ 客戶自助繳費入口。
5. **市場定位參考**：若目標客群是台灣中小型 B2B，PandaDoc 的「輕量、快速上線（1-2 週）、per-user 定價」路線比 Ironclad 的重企業流程更貼近，值得作為 MVP 範圍設定的錨點。
