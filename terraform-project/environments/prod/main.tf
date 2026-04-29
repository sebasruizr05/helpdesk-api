terraform {
  required_version = ">= 1.6.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

variable "project_id" {
  type = string
}

variable "region" {
  type    = string
  default = "us-central1"
}

variable "zone" {
  type    = string
  default = "us-central1-a"
}

variable "ssh_public_key" {
  type      = string
  sensitive = true
}

variable "db_password" {
  type      = string
  sensitive = true
}

module "stack" {
  source = "../.."

  project_id           = var.project_id
  environment          = "prod"
  region               = var.region
  zone                 = var.zone
  resource_prefix      = "helpdesk-prod"
  storage_bucket_name  = "${var.project_id}-helpdesk-prod-artifacts"
  bastion_machine_type = "e2-small"
  db_tier              = "db-custom-2-7680"
  bastion_disk_size_gb = 30
  db_disk_size_gb      = 30
  ssh_public_key       = var.ssh_public_key
  db_password          = var.db_password
  labels = {
    owner = "devops-course"
    stack = "terraform-prod"
  }
}

output "bastion_public_ip" {
  value = module.stack.bastion_public_ip
}

output "bastion_name" {
  value = module.stack.bastion_name
}

output "cloud_sql_public_ip" {
  value = module.stack.cloud_sql_public_ip
}
