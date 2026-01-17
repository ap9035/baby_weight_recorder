# ==============================================================================
# Provider 設定
# ==============================================================================

provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}

# ==============================================================================
# 啟用必要的 GCP API
# ==============================================================================

resource "google_project_service" "apis" {
  for_each = toset([
    "run.googleapis.com",                  # Cloud Run
    "artifactregistry.googleapis.com",     # Artifact Registry
    "firestore.googleapis.com",            # Firestore
    "secretmanager.googleapis.com",        # Secret Manager
    "apigateway.googleapis.com",           # API Gateway
    "servicecontrol.googleapis.com",       # Service Control (API Gateway 需要)
    "servicemanagement.googleapis.com",    # Service Management (API Gateway 需要)
    "iam.googleapis.com",                  # IAM
    "iamcredentials.googleapis.com",       # IAM Credentials (Workload Identity)
    "cloudresourcemanager.googleapis.com", # Resource Manager
  ])

  project = var.project_id
  service = each.value

  disable_on_destroy = false
}

# ==============================================================================
# Artifact Registry
# ==============================================================================

module "artifact_registry" {
  source = "./modules/artifact-registry"

  project_id  = var.project_id
  region      = var.region
  environment = var.environment

  depends_on = [google_project_service.apis]
}

# ==============================================================================
# Secret Manager
# ==============================================================================

module "secret_manager" {
  source = "./modules/secret-manager"

  project_id  = var.project_id
  environment = var.environment

  depends_on = [google_project_service.apis]
}

# ==============================================================================
# Firestore
# ==============================================================================

module "firestore" {
  source = "./modules/firestore"

  project_id  = var.project_id
  region      = var.region
  environment = var.environment

  depends_on = [google_project_service.apis]
}

# ==============================================================================
# Cloud Run - Auth Service
# ==============================================================================

module "auth_service" {
  source = "./modules/cloud-run"

  project_id   = var.project_id
  region       = var.region
  environment  = var.environment
  service_name = var.auth_service_name

  # 使用 placeholder image，CI/CD 會更新為實際 image
  image = "gcr.io/cloudrun/hello"

  cpu           = var.cloud_run_cpu
  memory        = var.cloud_run_memory
  min_instances = var.cloud_run_min_instances
  max_instances = var.cloud_run_max_instances

  env_vars = {
    ENVIRONMENT    = var.environment
    JWT_ISSUER     = var.jwt_issuer
    JWT_AUDIENCE   = var.jwt_audience
    GCP_PROJECT_ID = var.project_id
  }

  secret_env_vars = {
    JWT_PRIVATE_KEY = module.secret_manager.jwt_private_key_secret_id
    INVITE_CODES    = module.secret_manager.invite_codes_secret_id
  }

  allow_unauthenticated = true # Auth endpoints 需要公開存取

  depends_on = [
    google_project_service.apis,
    module.artifact_registry,
    module.secret_manager,
  ]
}

# ==============================================================================
# Cloud Run - Weight API Service
# ==============================================================================

module "api_service" {
  source = "./modules/cloud-run"

  project_id   = var.project_id
  region       = var.region
  environment  = var.environment
  service_name = var.api_service_name

  # 使用 placeholder image，CI/CD 會更新為實際 image
  image = "gcr.io/cloudrun/hello"

  cpu           = var.cloud_run_cpu
  memory        = var.cloud_run_memory
  min_instances = var.cloud_run_min_instances
  max_instances = var.cloud_run_max_instances

  env_vars = {
    ENVIRONMENT    = var.environment
    AUTH_JWKS_URL  = "${module.auth_service.service_url}/.well-known/jwks.json"
    JWT_ISSUER     = var.jwt_issuer
    JWT_AUDIENCE   = var.jwt_audience
    GCP_PROJECT_ID = var.project_id
  }

  secret_env_vars = {}

  allow_unauthenticated = false # 需要透過 API Gateway 存取
  # 授予 Kong Gateway Service Account 調用權限
  service_account_invokers = [module.kong_gateway.service_account_email]

  depends_on = [
    google_project_service.apis,
    module.artifact_registry,
    module.auth_service,
    module.kong_gateway,
  ]
}

# ==============================================================================
# Kong Gateway (替代 GCP API Gateway)
# ==============================================================================
# Kong 部署為獨立 Cloud Run 服務，使用 DB-less mode
# 優點：支援 asia-east1、低延遲、功能豐富
# 詳見：docs/baby_weight_recorder-spec.md

module "kong_gateway" {
  source = "./modules/kong-gateway"

  project_id  = var.project_id
  region      = var.region
  environment = var.environment

  # 使用內部 URL 進行服務間通信（同專案內，免費且低延遲）
  auth_service_url = module.auth_service.internal_url
  api_service_url  = module.api_service.internal_url

  # 使用 placeholder image，CI/CD 會更新為實際 image
  kong_image = "gcr.io/cloudrun/hello"

  cpu           = var.cloud_run_cpu
  memory        = var.cloud_run_memory
  min_instances = var.cloud_run_min_instances
  max_instances = var.cloud_run_max_instances

  depends_on = [
    google_project_service.apis,
    module.auth_service,
    module.api_service,
  ]
}

# ==============================================================================
# Workload Identity (GitHub Actions)
# ==============================================================================

module "workload_identity" {
  source = "./modules/workload-identity"

  project_id  = var.project_id
  environment = var.environment
  github_repo = var.github_repo

  artifact_registry_repository = module.artifact_registry.repository_name
  cloud_run_services = [
    module.auth_service.service_name,
    module.api_service.service_name,
  ]

  depends_on = [google_project_service.apis]
}
