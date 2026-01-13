output "service_url" {
  description = "Kong Gateway URL"
  value       = google_cloud_run_v2_service.kong.uri
}

output "service_name" {
  description = "Kong Gateway service name"
  value       = google_cloud_run_v2_service.kong.name
}

output "service_account_email" {
  description = "Kong service account email"
  value       = google_service_account.kong.email
}
