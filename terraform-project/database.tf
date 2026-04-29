module "database" {
  source = "./modules/database"

  project_id          = var.project_id
  region              = var.region
  resource_prefix     = var.resource_prefix
  db_name             = var.db_name
  db_user             = var.db_user
  db_password         = var.db_password
  db_tier             = var.db_tier
  db_disk_size_gb     = var.db_disk_size_gb
  db_authorized_cidrs = var.db_authorized_cidrs
  labels              = local.common_labels

  depends_on = [module.network]
}
