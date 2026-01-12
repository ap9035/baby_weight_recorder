output "gateway_url" {
  description = "API Gateway URL"
  value       = "https://${google_api_gateway_gateway.gateway.default_hostname}"
}

output "gateway_id" {
  description = "API Gateway ID"
  value       = google_api_gateway_gateway.gateway.gateway_id
}

output "api_id" {
  description = "API ID"
  value       = google_api_gateway_api.api.api_id
}
