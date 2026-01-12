# API Gateway

# API Config (OpenAPI Spec)
resource "google_api_gateway_api" "api" {
  provider = google-beta
  project  = var.project_id
  api_id   = "baby-weight-api-${var.environment}"

  labels = {
    environment = var.environment
    app         = "baby-weight"
  }
}

resource "google_api_gateway_api_config" "config" {
  provider      = google-beta
  project       = var.project_id
  api           = google_api_gateway_api.api.api_id
  api_config_id = "baby-weight-config-${var.environment}-${formatdate("YYYYMMDDhhmmss", timestamp())}"

  openapi_documents {
    document {
      path     = "openapi.yaml"
      contents = base64encode(local.openapi_spec)
    }
  }

  gateway_config {
    backend_config {
      google_service_account = google_service_account.gateway.email
    }
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "google_api_gateway_gateway" "gateway" {
  provider   = google-beta
  project    = var.project_id
  region     = var.region
  api_config = google_api_gateway_api_config.config.id
  gateway_id = "baby-weight-gateway-${var.environment}"

  labels = {
    environment = var.environment
    app         = "baby-weight"
  }
}

# Service Account for API Gateway
resource "google_service_account" "gateway" {
  project      = var.project_id
  account_id   = "api-gateway-${var.environment}"
  display_name = "API Gateway (${var.environment})"
  description  = "Service account for API Gateway to invoke Cloud Run"
}

# Grant API Gateway permission to invoke Cloud Run
resource "google_project_iam_member" "gateway_invoker" {
  project = var.project_id
  role    = "roles/run.invoker"
  member  = "serviceAccount:${google_service_account.gateway.email}"
}

# OpenAPI Specification
locals {
  openapi_spec = <<-EOF
swagger: "2.0"
info:
  title: "Baby Weight Recorder API"
  description: "嬰兒體重紀錄系統 API Gateway"
  version: "1.0.0"
schemes:
  - "https"
produces:
  - "application/json"
securityDefinitions:
  jwt_auth:
    type: "oauth2"
    authorizationUrl: ""
    flow: "implicit"
    x-google-issuer: "${var.jwt_issuer}"
    x-google-jwks_uri: "${var.jwks_uri}"
    x-google-audiences: "${var.jwt_audience}"

paths:
  # ========================================
  # Auth Service (公開端點)
  # ========================================
  /auth/register:
    post:
      summary: "使用者註冊"
      operationId: "authRegister"
      x-google-backend:
        address: "${var.auth_service_url}/auth/register"
      responses:
        201:
          description: "註冊成功"

  /auth/token:
    post:
      summary: "使用者登入"
      operationId: "authToken"
      x-google-backend:
        address: "${var.auth_service_url}/auth/token"
      responses:
        200:
          description: "登入成功"

  /.well-known/jwks.json:
    get:
      summary: "JWKS 公鑰"
      operationId: "jwks"
      x-google-backend:
        address: "${var.auth_service_url}/.well-known/jwks.json"
      responses:
        200:
          description: "JWKS"

  # ========================================
  # Weight API Service (需要認證)
  # ========================================
  /v1/babies:
    get:
      summary: "列出嬰兒"
      operationId: "listBabies"
      security:
        - jwt_auth: []
      x-google-backend:
        address: "${var.api_service_url}/v1/babies"
      responses:
        200:
          description: "嬰兒列表"
    post:
      summary: "建立嬰兒"
      operationId: "createBaby"
      security:
        - jwt_auth: []
      x-google-backend:
        address: "${var.api_service_url}/v1/babies"
      responses:
        201:
          description: "建立成功"

  /v1/babies/{babyId}:
    get:
      summary: "取得嬰兒資訊"
      operationId: "getBaby"
      security:
        - jwt_auth: []
      x-google-backend:
        address: "${var.api_service_url}/v1/babies/{babyId}"
        path_translation: APPEND_PATH_TO_ADDRESS
      parameters:
        - name: babyId
          in: path
          required: true
          type: string
      responses:
        200:
          description: "嬰兒資訊"

  /v1/babies/{babyId}/weights:
    get:
      summary: "查詢體重紀錄"
      operationId: "listWeights"
      security:
        - jwt_auth: []
      x-google-backend:
        address: "${var.api_service_url}/v1/babies/{babyId}/weights"
        path_translation: APPEND_PATH_TO_ADDRESS
      parameters:
        - name: babyId
          in: path
          required: true
          type: string
      responses:
        200:
          description: "體重紀錄列表"
    post:
      summary: "新增體重紀錄"
      operationId: "createWeight"
      security:
        - jwt_auth: []
      x-google-backend:
        address: "${var.api_service_url}/v1/babies/{babyId}/weights"
        path_translation: APPEND_PATH_TO_ADDRESS
      parameters:
        - name: babyId
          in: path
          required: true
          type: string
      responses:
        201:
          description: "新增成功"

  /v1/babies/{babyId}/weights/{weightId}:
    put:
      summary: "修改體重紀錄"
      operationId: "updateWeight"
      security:
        - jwt_auth: []
      x-google-backend:
        address: "${var.api_service_url}/v1/babies/{babyId}/weights/{weightId}"
        path_translation: APPEND_PATH_TO_ADDRESS
      parameters:
        - name: babyId
          in: path
          required: true
          type: string
        - name: weightId
          in: path
          required: true
          type: string
      responses:
        200:
          description: "修改成功"
    delete:
      summary: "刪除體重紀錄"
      operationId: "deleteWeight"
      security:
        - jwt_auth: []
      x-google-backend:
        address: "${var.api_service_url}/v1/babies/{babyId}/weights/{weightId}"
        path_translation: APPEND_PATH_TO_ADDRESS
      parameters:
        - name: babyId
          in: path
          required: true
          type: string
        - name: weightId
          in: path
          required: true
          type: string
      responses:
        204:
          description: "刪除成功"

  /v1/babies/{babyId}/weights/{weightId}/assessment:
    get:
      summary: "成長曲線評估"
      operationId: "getWeightAssessment"
      security:
        - jwt_auth: []
      x-google-backend:
        address: "${var.api_service_url}/v1/babies/{babyId}/weights/{weightId}/assessment"
        path_translation: APPEND_PATH_TO_ADDRESS
      parameters:
        - name: babyId
          in: path
          required: true
          type: string
        - name: weightId
          in: path
          required: true
          type: string
      responses:
        200:
          description: "評估結果"

  # Health Check
  /health:
    get:
      summary: "健康檢查"
      operationId: "healthCheck"
      x-google-backend:
        address: "${var.api_service_url}/health"
      responses:
        200:
          description: "健康"
EOF
}
