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

  image = "${var.region}-docker.pkg.dev/${var.project_id}/${module.artifact_registry.repository_name}/${var.auth_service_name}:latest"

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

  image = "${var.region}-docker.pkg.dev/${var.project_id}/${module.artifact_registry.repository_name}/${var.api_service_name}:latest"

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

  depends_on = [
    google_project_service.apis,
    module.artifact_registry,
    module.auth_service,
  ]
}

# ==============================================================================
# API Gateway
# ==============================================================================

module "api_gateway" {
  source = "./modules/api-gateway"

  project_id  = var.project_id
  region      = var.region
  environment = var.environment

  auth_service_url = module.auth_service.service_url
  api_service_url  = module.api_service.service_url

  jwt_issuer   = var.jwt_issuer
  jwt_audience = var.jwt_audience
  jwks_uri     = "${module.auth_service.service_url}/.well-known/jwks.json"

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
