output "service_url" {
  description = "Kong Gateway public URL"
  value       = google_cloud_run_v2_service.kong.uri
}

output "service_account_email" {
  description = "Kong Gateway service account email"
  value       = google_service_account.kong.email
}
