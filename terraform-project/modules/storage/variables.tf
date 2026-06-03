variable "project_id" {
  type = string
}

variable "region" {
  type = string
}

variable "resource_prefix" {
  type = string
}

variable "storage_bucket_name" {
  type = string
}

variable "artifact_registry_repository_id" {
  type = string
}

variable "labels" {
  type    = map(string)
  default = {}
}
