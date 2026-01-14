output "service_name" {
  description = "Cloud Run Service 名稱"
  value       = google_cloud_run_v2_service.service.name
}

output "service_url" {
  description = "Cloud Run Service URL (公網 URL)"
  value       = google_cloud_run_v2_service.service.uri
}

output "internal_url" {
  description = "Cloud Run Service Internal URL (內部 URL，用於服務間通信)"
  # 內部 URL 格式: https://SERVICE_NAME-PROJECT_NUMBER.REGION.run.app
  # service.uri 在同專案內已經是內部 URL
  value = google_cloud_run_v2_service.service.uri
}

output "service_account_email" {
  description = "Service Account Email"
  value       = google_service_account.service.email
}
