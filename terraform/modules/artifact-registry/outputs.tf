output "repository_name" {
  description = "Artifact Registry Repository 名稱"
  value       = google_artifact_registry_repository.docker.repository_id
}

output "repository_url" {
  description = "Artifact Registry Repository URL"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.docker.repository_id}"
}
