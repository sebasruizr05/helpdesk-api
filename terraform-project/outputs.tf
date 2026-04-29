output "bastion_name" {
  description = "Nombre de la VM bastion."
  value       = module.compute.instance_name
}

output "bastion_public_ip" {
  description = "IP publica de la VM bastion."
  value       = module.compute.public_ip
}

output "bastion_ssh_command" {
  description = "Comando de referencia para conectarse por SSH."
  value       = "gcloud compute ssh ${var.ssh_username}@${module.compute.instance_name} --zone ${var.zone} --project ${var.project_id}"
}

output "cloud_sql_public_ip" {
  description = "IP publica de la instancia Cloud SQL."
  value       = module.database.public_ip_address
}

output "database_name" {
  description = "Nombre de la base de datos provisionada."
  value       = module.database.database_name
}

output "database_user" {
  description = "Usuario de base de datos."
  value       = module.database.database_user
}

output "artifact_registry_repository" {
  description = "Nombre del repositorio Docker."
  value       = module.storage.artifact_registry_repository
}

output "storage_bucket" {
  description = "Nombre del bucket GCS."
  value       = module.storage.storage_bucket_name
}
