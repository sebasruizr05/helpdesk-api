output "storage_bucket_name" {
  value = google_storage_bucket.artifacts.name
}

output "artifact_registry_repository" {
  value = google_artifact_registry_repository.docker.name
}
