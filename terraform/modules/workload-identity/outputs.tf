output "provider_name" {
  description = "Workload Identity Provider 完整名稱 (用於 GitHub Actions)"
  value       = google_iam_workload_identity_pool_provider.github.name
}

output "service_account_email" {
  description = "GitHub Actions Service Account Email"
  value       = google_service_account.github_actions.email
}

output "pool_name" {
  description = "Workload Identity Pool 名稱"
  value       = google_iam_workload_identity_pool.github.name
}
