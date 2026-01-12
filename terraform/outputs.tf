# ==============================================================================
# Service URLs
# ==============================================================================

output "auth_service_url" {
  description = "Auth Service URL"
  value       = module.auth_service.service_url
}

output "api_service_url" {
  description = "Weight API Service URL"
  value       = module.api_service.service_url
}

output "api_gateway_url" {
  description = "API Gateway URL"
  value       = module.api_gateway.gateway_url
}

# ==============================================================================
# Artifact Registry
# ==============================================================================

output "artifact_registry_repository" {
  description = "Artifact Registry Repository 名稱"
  value       = module.artifact_registry.repository_name
}

output "artifact_registry_url" {
  description = "Artifact Registry URL"
  value       = module.artifact_registry.repository_url
}

# ==============================================================================
# Workload Identity (GitHub Actions)
# ==============================================================================

output "workload_identity_provider" {
  description = "Workload Identity Provider (用於 GitHub Actions)"
  value       = module.workload_identity.provider_name
}

output "workload_identity_service_account" {
  description = "Service Account Email (用於 GitHub Actions)"
  value       = module.workload_identity.service_account_email
}

# ==============================================================================
# Firestore
# ==============================================================================

output "firestore_database" {
  description = "Firestore Database ID"
  value       = module.firestore.database_id
}
