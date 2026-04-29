variable "project_id" {
  type = string
}

variable "region" {
  type = string
}

variable "resource_prefix" {
  type = string
}

variable "network_self_link" {
  type = string
}

variable "db_name" {
  type = string
}

variable "db_user" {
  type = string
}

variable "db_password" {
  type      = string
  sensitive = true
}

variable "db_tier" {
  type = string
}

variable "db_disk_size_gb" {
  type = number
}

variable "labels" {
  type    = map(string)
  default = {}
}
