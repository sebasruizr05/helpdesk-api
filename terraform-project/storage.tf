module "storage" {
  source = "./modules/storage"

  project_id                      = var.project_id
  region                          = var.region
  resource_prefix                 = var.resource_prefix
  storage_bucket_name             = var.storage_bucket_name
  artifact_registry_repository_id = var.artifact_registry_repository_id
  labels                          = local.common_labels

  depends_on = [google_project_service.required]
}
