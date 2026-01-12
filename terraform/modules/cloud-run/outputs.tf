output "service_name" {
  description = "Cloud Run Service 名稱"
  value       = google_cloud_run_v2_service.service.name
}

output "service_url" {
  description = "Cloud Run Service URL"
  value       = google_cloud_run_v2_service.service.uri
}

output "service_account_email" {
  description = "Service Account Email"
  value       = google_service_account.service.email
}
