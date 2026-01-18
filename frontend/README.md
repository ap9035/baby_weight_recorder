# 嬰兒成長曲線前端

純 HTML/CSS/JavaScript 單頁應用，用於顯示嬰兒體重成長曲線。

## 功能

- ✅ 登入/登出（JWT Token 認證）
- ✅ 顯示成長曲線圖表（使用 Chart.js）
- ✅ 顯示評估結果（百分位數、評估等級、建議）
- ✅ 刷新按鈕（重新載入數據）
- ✅ 響應式設計（支援手機、平板、電腦）

## 檔案結構

```
frontend/
├── index.html          # 主頁面（單頁應用）
├── css/
│   └── style.css      # 樣式表
├── js/
│   ├── auth.js        # 登入/登出邏輯
│   ├── api.js         # API 呼叫
│   ├── chart.js       # 圖表繪製（Chart.js）
│   └── main.js        # 主要應用邏輯
├── assets/            # 靜態資源（圖片、字體等）
└── README.md          # 本文件
```

## 使用方法

### 本地測試

1. 使用 Python HTTP 伺服器：
```bash
cd frontend
python3 -m http.server 8000
```

2. 開啟瀏覽器：
```
http://localhost:8000
```

### 部署到 GCS（Google Cloud Storage）

1. 建立 GCS Bucket：
```bash
gsutil mb gs://baby-weight-frontend-dev
```

2. 設定靜態網站託管：
```bash
gsutil web set -m index.html -e index.html gs://baby-weight-frontend-dev
```

3. 上傳檔案：
```bash
gsutil -m rsync -r frontend/ gs://baby-weight-frontend-dev/
```

4. 設定公開讀取（或使用 IAM）：
```bash
gsutil iam ch allUsers:objectViewer gs://baby-weight-frontend-dev
```

5. 存取網址：
```
https://storage.googleapis.com/baby-weight-frontend-dev/index.html
```

## 使用說明

1. **登入**：
   - 輸入 Email 和密碼
   - 點擊「登入」按鈕
   - Token 會自動儲存到 localStorage

2. **查看成長曲線**：
   - 輸入 Baby ID
   - 點擊「🔄 刷新」按鈕或按 Enter
   - 圖表會自動更新

3. **登出**：
   - 點擊「登出」按鈕
   - Token 會自動清除

## API 端點

- **登入**：`POST /auth/token`
- **取得體重記錄**：`GET /v1/babies/{baby_id}/weights?include_assessment=true`

## 注意事項

- Token 儲存在 `localStorage`，關閉瀏覽器後仍保留
- Token 過期時會自動要求重新登入
- Baby ID 會自動儲存，下次開啟時自動填入

## 依賴

- [Chart.js](https://www.chartjs.org/) - 圖表庫（使用 CDN）
- 原生 JavaScript（無需建置工具）
