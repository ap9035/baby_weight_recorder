# Firestore Database (Native Mode)

resource "google_firestore_database" "database" {
  project     = var.project_id
  name        = var.environment == "prod" ? "(default)" : var.environment
  location_id = var.region
  type        = "FIRESTORE_NATIVE"

  # 啟用刪除保護 (生產環境)
  delete_protection_state = var.environment == "prod" ? "DELETE_PROTECTION_ENABLED" : "DELETE_PROTECTION_DISABLED"

  # Point-in-time recovery (生產環境)
  point_in_time_recovery_enablement = var.environment == "prod" ? "POINT_IN_TIME_RECOVERY_ENABLED" : "POINT_IN_TIME_RECOVERY_DISABLED"
}

# ==============================================================================
# Firestore Indexes
# ==============================================================================

# identity_links: 查詢 issuer + subject
resource "google_firestore_index" "identity_links_by_iss_sub" {
  project    = var.project_id
  database   = google_firestore_database.database.name
  collection = "identity_links"

  fields {
    field_path = "iss"
    order      = "ASCENDING"
  }

  fields {
    field_path = "sub"
    order      = "ASCENDING"
  }
}

# babies: 依 createdAt 排序
resource "google_firestore_index" "babies_by_created_at" {
  project    = var.project_id
  database   = google_firestore_database.database.name
  collection = "babies"

  fields {
    field_path = "createdAt"
    order      = "DESCENDING"
  }
}

# weights: 依 babyId + recordedAt 查詢
resource "google_firestore_index" "weights_by_baby_and_date" {
  project    = var.project_id
  database   = google_firestore_database.database.name
  collection = "weights"

  fields {
    field_path = "babyId"
    order      = "ASCENDING"
  }

  fields {
    field_path = "recordedAt"
    order      = "DESCENDING"
  }
}

# memberships: 依 userId 查詢
resource "google_firestore_index" "memberships_by_user" {
  project    = var.project_id
  database   = google_firestore_database.database.name
  collection = "memberships"

  fields {
    field_path = "userId"
    order      = "ASCENDING"
  }

  fields {
    field_path = "babyId"
    order      = "ASCENDING"
  }
}

# memberships: 依 babyId 查詢
resource "google_firestore_index" "memberships_by_baby" {
  project    = var.project_id
  database   = google_firestore_database.database.name
  collection = "memberships"

  fields {
    field_path = "babyId"
    order      = "ASCENDING"
  }

  fields {
    field_path = "role"
    order      = "ASCENDING"
  }
}
