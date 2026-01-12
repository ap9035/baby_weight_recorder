output "database_id" {
  description = "Firestore Database ID"
  value       = google_firestore_database.database.name
}

output "database_location" {
  description = "Firestore Database Location"
  value       = google_firestore_database.database.location_id
}
