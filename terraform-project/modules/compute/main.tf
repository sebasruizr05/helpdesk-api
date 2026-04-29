resource "google_compute_instance" "bastion" {
  name         = "${var.resource_prefix}-bastion"
  machine_type = var.machine_type
  zone         = var.zone
  tags         = ["${var.resource_prefix}-bastion"]
  labels       = var.labels

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-12"
      size  = var.disk_size_gb
      type  = "pd-balanced"
    }
  }

  network_interface {
    subnetwork = var.subnet_self_link

    access_config {}
  }

  metadata = {
    ssh-keys = "${var.ssh_username}:${var.ssh_public_key}"
  }

  metadata_startup_script = <<-EOT
    #!/bin/bash
    set -eux
    export DEBIAN_FRONTEND=noninteractive
    apt-get update
    apt-get install -y postgresql-client
  EOT

  dynamic "service_account" {
    for_each = var.service_account_email == null ? [] : [var.service_account_email]

    content {
      email  = service_account.value
      scopes = ["cloud-platform"]
    }
  }
}
