variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "environment" {
  description = "環境名稱 (dev, prod)"
  type        = string
}

variable "github_repo" {
  description = "GitHub Repository (格式: owner/repo)"
  type        = string
}

variable "artifact_registry_repository" {
  description = "Artifact Registry Repository 名稱"
  type        = string
}

variable "cloud_run_services" {
  description = "Cloud Run Service 名稱列表"
  type        = list(string)
  default     = []
}
