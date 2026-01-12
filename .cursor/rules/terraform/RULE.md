---
description: Terraform 基礎設施規範
globs:
  - "**/*.tf"
  - "**/*.tfvars"
alwaysApply: false
---

# Terraform 規範

## 檔案結構

```
terraform/
├── main.tf           # 主要資源定義
├── variables.tf      # 變數宣告
├── outputs.tf        # 輸出值
├── versions.tf       # Provider 版本
├── environments/
│   ├── dev.tfvars
│   └── prod.tfvars
└── modules/
    ├── cloud-run/
    ├── firestore/
    └── api-gateway/
```

## 命名規範

- 資源名稱使用 snake_case
- 變數名稱使用 snake_case
- 環境標籤: `dev`, `prod`

## 狀態管理

使用 GCS Backend：

```hcl
terraform {
  backend "gcs" {
    bucket = "baby-weight-tf-state"
    prefix = "terraform/state"
  }
}
```

## 機敏資料

- 使用 Secret Manager 儲存機敏資料
- 不在 .tfvars 中儲存密碼或 API Key
- 確保 .tfvars 加入 .gitignore
