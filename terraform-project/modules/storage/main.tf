resource "google_storage_bucket" "artifacts" {
  name                        = var.storage_bucket_name
  location                    = var.region
  project                     = var.project_id
  uniform_bucket_level_access = true
  force_destroy               = true
  labels                      = var.labels
}

resource "google_artifact_registry_repository" "docker" {
  location      = var.region
  project       = var.project_id
  repository_id = var.artifact_registry_repository_id
  format        = "DOCKER"
  description   = "Repositorio Docker para la sustentacion Terraform"
  labels        = var.labels
}
