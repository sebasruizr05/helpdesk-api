output "instance_name" {
  value = google_sql_database_instance.postgres.name
}

output "public_ip_address" {
  value = google_sql_database_instance.postgres.public_ip_address
}

output "database_name" {
  value = google_sql_database.database.name
}

output "database_user" {
  value = google_sql_user.user.name
}
