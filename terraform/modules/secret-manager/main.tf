# Secret Manager secrets for sensitive data

# JWT Private Key
resource "google_secret_manager_secret" "jwt_private_key" {
  project   = var.project_id
  secret_id = "jwt-private-key-${var.environment}"

  replication {
    auto {}
  }

  labels = {
    environment = var.environment
    app         = "baby-weight"
  }
}

# Invite Codes
resource "google_secret_manager_secret" "invite_codes" {
  project   = var.project_id
  secret_id = "invite-codes-${var.environment}"

  replication {
    auto {}
  }

  labels = {
    environment = var.environment
    app         = "baby-weight"
  }
}

# Note: Secret versions (actual secret values) should be created manually
# or via CI/CD pipeline, not in Terraform to avoid storing secrets in state
