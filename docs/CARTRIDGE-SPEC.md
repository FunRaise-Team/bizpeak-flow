# BizPeak Flow — 卡帶規範 v0.1（Cartridge Spec）

> 這份文件回答一個問題：**AI 先鋒計畫的同仁 Vibe Code 出一個好用的小工具之後、怎麼讓它「插上主機」變成公司資產、而不是又一個孤島。**
> 上位文件：`CONSTITUTION.md` 第三條（卡帶合規、主幹道不分岔）。

---

## 1. 什麼是卡帶

一個卡帶 = 一個功能模組。合約生命週期是第一個卡帶；未來的採購流程、請假流程、廠商管理、任何同仁自己長出來的小流程、都可以是卡帶。

**主機提供**（卡帶不用自己做）：資料層存取（Notion 權威源 + 快取）、狀態機引擎、事件匯流排、通知服務、排程器、三種介面的接入面（GUI 路由 / Agent 工具 / MCP tool）、權限與稽核。

**卡帶提供**：自己的業務邏輯、自己的資料契約、自己的畫面（可選）。

## 2. 卡帶四件套（接入契約、缺一不上主幹道）

### ① Manifest（卡帶身分證）

```yaml
name: contract-lifecycle          # 卡帶名（kebab-case）
owner: allen.hung                 # 有名有姓的 owner、離職必轉移
version: 0.1.0
level: L2                         # L0 私人 / L1 團隊 / L2 全公司
description: 合約生命週期閉環（報價 → 簽核 → 收款 → 續約）
databases: [contracts, payments]  # 用到的資料契約（見②）
capabilities: [contract.create, contract.transition, payment.mark_paid]
events:
  publishes: [contract.signed, payment.overdue]
  subscribes: [quote.created]
```

### ② 資料契約（Schema Registry）

- 卡帶用到的每個 Notion database 欄位（名稱、型別、關聯）**先註冊進 Cartridges DB、再動手**
- 禁止影子欄位：不得在別人的 database 私加欄位；要共用欄位、先在 registry 對齊
- Why：立項會議明列風險「各單位點狀工具資料格式不一致」— registry 就是解方

### ③ 能力層（Capabilities）

- 每個功能動作 = 一個具名能力：TypeScript 函式 + REST 路由 + MCP tool、三位一體（憲法第二條）
- 能力必須宣告：輸入 / 輸出 schema、需要的角色權限、是否需要人審（憲法第四條動作標記 `requires_human: true`）
- 寫入 Notion 一律經過主機的 trusted bridge、卡帶不得自帶 token 直寫

### ④ 事件（Events）

- 卡帶之間**只透過事件說話**、不互相 import — 合約卡帶發 `payment.overdue`、催收卡帶訂閱它、兩者互不認識
- 事件必落 Events DB（audit trail、憲法第五條）

## 3. 三級接入制（讓 Vibe Coding 有出口、也有關卡）

| 等級 | 誰能用 | 接入要求 | 審查 |
|------|--------|----------|------|
| **L0 私人卡帶** | 只有開發者本人 | Manifest + 不碰共用資料的寫入 | 免審、註冊即用 |
| **L1 團隊卡帶** | 單一團隊 / BU | 四件套齊 + 資料契約通過 registry 檢查 | 卡帶 owner + 平台維護者 |
| **L2 全公司卡帶** | 全公司 | L1 全部 + 安全檢查（憲法第七條）+ 一次真實資料驗證（憲法第五條證據） | Decision Owner 拍板 |

**升級路徑就是先鋒計畫的出口**：同仁自己 Vibe Code（L0）→ 團隊覺得好用（L1）→ 公司採納（L2）。每一級都有明確驗收、不再是「做得好但接不進來」。

## 4. 開發者體驗（規劃、1.0 之後落地)

- `cartridge-template/`：範本 repo（manifest 骨架、能力範例、測試骨架）
- `bizpeak validate`：接入前自檢（manifest 完整性、schema 衝突、權限宣告）
- 範例卡帶：合約生命週期本身就是參考實作 — 第一個卡帶怎麼寫、後面的照抄

## 5. 治理

- Cartridges DB 是卡帶的戶口名簿：誰的、幾級、動哪些資料、暴露哪些能力 — 全公司可查
- 卡帶 owner 離職 → 卡帶必轉移或降級歸檔（教育訓練成本與離職風險、本專案的立項初衷）
- 平台層（主機）改動需 Decision Owner 拍板；卡帶層各自演化
