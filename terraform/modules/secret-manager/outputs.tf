output "jwt_private_key_secret_id" {
  description = "JWT Private Key Secret ID"
  value       = google_secret_manager_secret.jwt_private_key.secret_id
}

output "invite_codes_secret_id" {
  description = "Invite Codes Secret ID"
  value       = google_secret_manager_secret.invite_codes.secret_id
}
