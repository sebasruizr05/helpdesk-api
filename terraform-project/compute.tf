module "compute" {
  source = "./modules/compute"

  project_id            = var.project_id
  zone                  = var.zone
  resource_prefix       = var.resource_prefix
  machine_type          = var.bastion_machine_type
  disk_size_gb          = var.bastion_disk_size_gb
  subnet_self_link      = module.network.subnet_self_link
  ssh_username          = var.ssh_username
  ssh_public_key        = var.ssh_public_key
  service_account_email = null
  labels                = local.common_labels

  depends_on = [module.network]
}
