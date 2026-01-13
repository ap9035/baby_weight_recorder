variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "gateway_region" {
  description = "API Gateway Region (asia-east1 不支援，使用 asia-northeast1)"
  type        = string
  default     = "asia-northeast1"
}

variable "environment" {
  description = "環境名稱 (dev, prod)"
  type        = string
}

variable "auth_service_url" {
  description = "Auth Service URL"
  type        = string
}

variable "api_service_url" {
  description = "Weight API Service URL"
  type        = string
}

variable "jwt_issuer" {
  description = "JWT Issuer URL"
  type        = string
}

variable "jwt_audience" {
  description = "JWT Audience"
  type        = string
}

variable "jwks_uri" {
  description = "JWKS URI"
  type        = string
}
