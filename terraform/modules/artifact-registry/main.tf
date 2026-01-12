# Artifact Registry Repository for Docker images

resource "google_artifact_registry_repository" "docker" {
  project       = var.project_id
  location      = var.region
  repository_id = "baby-weight-${var.environment}"
  description   = "Docker images for Baby Weight Recorder (${var.environment})"
  format        = "DOCKER"

  cleanup_policies {
    id     = "keep-recent"
    action = "KEEP"

    most_recent_versions {
      keep_count = 10
    }
  }
}
