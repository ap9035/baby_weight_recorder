#!/bin/bash
# 為 GitHub Actions Service Account 添加 Storage 權限

PROJECT_ID="babyweightrecorder"
SERVICE_ACCOUNT="github-actions-dev@babyweightrecorder.iam.gserviceaccount.com"

echo "🔐 為 Service Account 添加 Storage 權限..."
echo "Service Account: $SERVICE_ACCOUNT"

# 添加 Storage Admin 角色（包含 bucket 創建和管理權限）
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/storage.admin" \
    --condition=None

echo ""
echo "✅ 已添加 Storage Admin 角色"
echo ""
echo "權限包含："
echo "  - storage.buckets.create"
echo "  - storage.buckets.get"
echo "  - storage.buckets.list"
echo "  - storage.objects.create"
echo "  - storage.objects.get"
echo "  - storage.objects.list"
echo "  - storage.objects.update"
echo "  - storage.objects.delete"
