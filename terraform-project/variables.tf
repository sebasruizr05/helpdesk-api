variable "project_id" {
  description = "ID del proyecto GCP donde se desplegara la infraestructura."
  type        = string
}

variable "environment" {
  description = "Nombre del ambiente."
  type        = string
}

variable "region" {
  description = "Region principal."
  type        = string
}

variable "zone" {
  description = "Zona principal para el bastion."
  type        = string
}

variable "resource_prefix" {
  description = "Prefijo comun para los recursos."
  type        = string
}

variable "network_cidr" {
  description = "CIDR de la subred principal."
  type        = string
  default     = "10.10.0.0/24"
}

variable "private_service_cidr" {
  description = "CIDR reservado para peering privado de Cloud SQL."
  type        = string
  default     = "10.20.0.0/16"
}

variable "ssh_username" {
  description = "Usuario que se usara para la conexion SSH."
  type        = string
  default     = "bastion"
}

variable "ssh_public_key" {
  description = "Llave publica SSH en formato OpenSSH."
  type        = string
  sensitive   = true
}

variable "ssh_source_ranges" {
  description = "Rangos CIDR permitidos para SSH."
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "bastion_machine_type" {
  description = "Tipo de maquina del bastion."
  type        = string
  default     = "e2-micro"
}

variable "bastion_disk_size_gb" {
  description = "Tamano del disco del bastion."
  type        = number
  default     = 20
}

variable "db_name" {
  description = "Nombre de la base de datos."
  type        = string
  default     = "helpdesk"
}

variable "db_user" {
  description = "Usuario de base de datos."
  type        = string
  default     = "helpdesk_user"
}

variable "db_password" {
  description = "Password del usuario de base de datos."
  type        = string
  sensitive   = true
}

variable "db_tier" {
  description = "Tier de Cloud SQL."
  type        = string
  default     = "db-f1-micro"
}

variable "db_disk_size_gb" {
  description = "Tamano del disco de Cloud SQL."
  type        = number
  default     = 20
}

variable "artifact_registry_repository_id" {
  description = "ID del repositorio de Artifact Registry."
  type        = string
  default     = "helpdesk-images"
}

variable "storage_bucket_name" {
  description = "Nombre del bucket GCS."
  type        = string
}

variable "labels" {
  description = "Etiquetas comunes para todos los recursos."
  type        = map(string)
  default     = {}
}
