module "database" {
  source = "./modules/database"

  project_id        = var.project_id
  region            = var.region
  resource_prefix   = var.resource_prefix
  network_self_link = module.network.network_self_link
  db_name           = var.db_name
  db_user           = var.db_user
  db_password       = var.db_password
  db_tier           = var.db_tier
  db_disk_size_gb   = var.db_disk_size_gb
  labels            = local.common_labels

  depends_on = [module.network]
}
