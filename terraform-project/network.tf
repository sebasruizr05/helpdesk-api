module "network" {
  source = "./modules/network"

  project_id           = var.project_id
  region               = var.region
  resource_prefix      = var.resource_prefix
  network_cidr         = var.network_cidr
  private_service_cidr = var.private_service_cidr
  ssh_source_ranges    = var.ssh_source_ranges
  labels               = local.common_labels

  depends_on = [google_project_service.required]
}
