output "jwt_private_key_secret_id" {
  description = "JWT Private Key Secret ID (full name for Cloud Run)"
  value       = google_secret_manager_secret.jwt_private_key.name
}

output "invite_codes_secret_id" {
  description = "Invite Codes Secret ID (full name for Cloud Run)"
  value       = google_secret_manager_secret.invite_codes.name
}
