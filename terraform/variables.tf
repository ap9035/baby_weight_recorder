# ==============================================================================
# Project 設定
# ==============================================================================

variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "asia-east1"
}

variable "environment" {
  description = "環境名稱 (dev, prod)"
  type        = string
  validation {
    condition     = contains(["dev", "prod"], var.environment)
    error_message = "Environment must be 'dev' or 'prod'."
  }
}

# ==============================================================================
# 服務設定
# ==============================================================================

variable "api_service_name" {
  description = "Weight API Service 名稱"
  type        = string
  default     = "weight-api"
}

variable "auth_service_name" {
  description = "Auth Service 名稱"
  type        = string
  default     = "auth-service"
}

# ==============================================================================
# Cloud Run 設定
# ==============================================================================

variable "cloud_run_cpu" {
  description = "Cloud Run CPU 配置"
  type        = string
  default     = "1"
}

variable "cloud_run_memory" {
  description = "Cloud Run Memory 配置"
  type        = string
  default     = "512Mi"
}

variable "cloud_run_min_instances" {
  description = "Cloud Run 最小實例數"
  type        = number
  default     = 0
}

variable "cloud_run_max_instances" {
  description = "Cloud Run 最大實例數"
  type        = number
  default     = 10
}

# ==============================================================================
# Auth 設定
# ==============================================================================

variable "jwt_issuer" {
  description = "JWT Issuer URL"
  type        = string
}

variable "jwt_audience" {
  description = "JWT Audience"
  type        = string
  default     = "baby-weight-api"
}

# ==============================================================================
# GitHub Actions 設定 (Workload Identity)
# ==============================================================================

variable "github_repo" {
  description = "GitHub Repository (格式: owner/repo)"
  type        = string
}
