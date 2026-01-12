# Terraform Backend 設定 - Prod 環境
# 使用方式: terraform init -backend-config=environments/backend-prod.hcl

bucket = "your-project-id-tf-state"  # 替換為你的 bucket 名稱
prefix = "baby-weight/prod"
