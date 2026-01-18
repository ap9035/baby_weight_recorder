#!/bin/bash
# 部署前端到 GCS（Google Cloud Storage）

set -e

PROJECT_ID="babyweightrecorder"
BUCKET_NAME="baby-weight-frontend-dev"
REGION="asia-east1"

echo "🚀 開始部署前端到 GCS..."

# 檢查 gcloud 是否已安裝
if ! command -v gcloud &> /dev/null; then
    echo "❌ 錯誤：未安裝 gcloud CLI"
    echo "請先安裝 Google Cloud SDK: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# 設定專案
echo "📌 設定 GCP 專案：$PROJECT_ID"
gcloud config set project $PROJECT_ID

# 檢查 bucket 是否存在，不存在則創建
if ! gsutil ls -b gs://$BUCKET_NAME &> /dev/null; then
    echo "📦 創建 GCS Bucket：$BUCKET_NAME"
    gsutil mb -l $REGION -p $PROJECT_ID gs://$BUCKET_NAME
    
    # 設定靜態網站託管
    echo "🌐 設定靜態網站託管..."
    gsutil web set -m index.html -e index.html gs://$BUCKET_NAME
    
    # 設定公開讀取權限
    echo "🔓 設定公開讀取權限..."
    gsutil iam ch allUsers:objectViewer gs://$BUCKET_NAME
else
    echo "✅ Bucket 已存在：$BUCKET_NAME"
fi

# 上傳檔案
echo "📤 上傳前端檔案到 GCS..."
gsutil -m rsync -r -d frontend/ gs://$BUCKET_NAME/

# 設定檔案權限和 metadata
echo "⚙️  設定檔案權限和 metadata..."
gsutil -m setmeta -h "Cache-Control:public, max-age=3600" gs://$BUCKET_NAME/**/*.js gs://$BUCKET_NAME/**/*.css || true
gsutil -m setmeta -h "Cache-Control:public, max-age=0" gs://$BUCKET_NAME/index.html || true

echo ""
echo "✅ 前端部署完成！"
echo "🌐 網址："
echo "   https://storage.googleapis.com/$BUCKET_NAME/index.html"
echo ""
echo "💡 如需自訂網域，請設定 CNAME 指向 c.storage.googleapis.com"
