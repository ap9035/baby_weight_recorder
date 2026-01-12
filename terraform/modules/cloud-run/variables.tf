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

variable "service_name" {
  description = "Service 名稱"
  type        = string
}

variable "image" {
  description = "Container Image URL"
  type        = string
}

variable "cpu" {
  description = "CPU 配置"
  type        = string
  default     = "1"
}

variable "memory" {
  description = "Memory 配置"
  type        = string
  default     = "512Mi"
}

variable "min_instances" {
  description = "最小實例數"
  type        = number
  default     = 0
}

variable "max_instances" {
  description = "最大實例數"
  type        = number
  default     = 10
}

variable "env_vars" {
  description = "環境變數"
  type        = map(string)
  default     = {}
}

variable "secret_env_vars" {
  description = "Secret 環境變數 (name -> secret_id)"
  type        = map(string)
  default     = {}
}

variable "allow_unauthenticated" {
  description = "是否允許未認證存取"
  type        = bool
  default     = false
}
