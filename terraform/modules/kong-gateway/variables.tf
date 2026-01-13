variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
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

variable "kong_image" {
  description = "Kong container image"
  type        = string
  default     = "kong:3.6-alpine"
}

variable "cpu" {
  description = "CPU limit"
  type        = string
  default     = "1"
}

variable "memory" {
  description = "Memory limit"
  type        = string
  default     = "512Mi"
}

variable "min_instances" {
  description = "Minimum number of instances"
  type        = number
  default     = 0
}

variable "max_instances" {
  description = "Maximum number of instances"
  type        = number
  default     = 10
}
