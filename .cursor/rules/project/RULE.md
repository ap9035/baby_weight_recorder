---
description: 嬰兒體重紀錄系統專案規則 - 包含開發規範與進度追蹤指引
alwaysApply: true
---

# 專案規則

## 專案概述

這是一個嬰兒體重紀錄系統，使用以下技術：
- **後端**: Python 3.12+ / FastAPI
- **資料庫**: Firestore (Native Mode)
- **部署**: GCP Cloud Run
- **基礎設施**: Terraform
- **CI/CD**: GitHub Actions

## 開發規範

### Python 開發
- 所有程式碼必須使用完整的 **Type Hints**
- 使用 **Pydantic v2** 進行資料驗證
- 使用 **Ruff** 進行 linting 和格式化
- 使用 **MyPy** (strict mode) 進行型別檢查
- 使用 **uv** 進行套件管理

### 程式碼風格
- 遵循 PEP 8 規範
- 函式和類別必須有 docstring
- 變數命名使用 snake_case
- 類別命名使用 PascalCase

## 進度追蹤 ⚠️ 重要

**完成任何開發任務後，必須更新專案進度文件：**

1. 開啟 `docs/PROJECT_ROADMAP.md`
2. 找到對應的任務項目
3. 將狀態從 `⬜ 待開始` 改為：
   - `🔄 進行中`：任務進行中
   - `✅ 完成`：任務完成
   - `❌ 取消`：任務取消
4. 更新「進度追蹤 > 統計」表格中的數字
5. 如有需要，在「更新紀錄」區塊新增一筆紀錄

## 相關文件

- 技術規格書: `docs/baby_weight_recorder-spec.md`
- 專案時程: `docs/PROJECT_ROADMAP.md`
