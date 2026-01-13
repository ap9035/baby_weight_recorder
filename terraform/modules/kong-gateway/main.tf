# Kong Gateway on Cloud Run
# 使用 Kong 作為 API 閘道，替代 GCP API Gateway

# Service Account for Kong
resource "google_service_account" "kong" {
  project      = var.project_id
  account_id   = "kong-gateway-${var.environment}"
  display_name = "Kong Gateway (${var.environment})"
  description  = "Service account for Kong Gateway to invoke Cloud Run services"
}

# Grant Kong permission to invoke Cloud Run services
resource "google_project_iam_member" "kong_invoker" {
  project = var.project_id
  role    = "roles/run.invoker"
  member  = "serviceAccount:${google_service_account.kong.email}"
}

# Cloud Run Service for Kong Gateway
resource "google_cloud_run_v2_service" "kong" {
  name     = "kong-gateway-${var.environment}"
  location = var.region
  project  = var.project_id

  template {
    service_account = google_service_account.kong.email

    containers {
      image = var.kong_image

      ports {
        container_port = 8000
      }

      env {
        name  = "KONG_DATABASE"
        value = "off"
      }

      env {
        name  = "KONG_DECLARATIVE_CONFIG"
        value = "/kong/kong.yml"
      }

      env {
        name  = "KONG_PROXY_ACCESS_LOG"
        value = "/dev/stdout"
      }

      env {
        name  = "KONG_PROXY_ERROR_LOG"
        value = "/dev/stderr"
      }

      env {
        name  = "AUTH_SERVICE_URL"
        value = var.auth_service_url
      }

      env {
        name  = "API_SERVICE_URL"
        value = var.api_service_url
      }

      resources {
        limits = {
          cpu    = var.cpu
          memory = var.memory
        }
      }
    }

    scaling {
      min_instance_count = var.min_instances
      max_instance_count = var.max_instances
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  labels = {
    environment = var.environment
    app         = "baby-weight"
    component   = "gateway"
  }
}

# Allow public access to Kong Gateway
resource "google_cloud_run_v2_service_iam_member" "kong_public" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.kong.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
