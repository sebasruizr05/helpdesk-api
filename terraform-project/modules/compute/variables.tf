variable "project_id" {
  type = string
}

variable "zone" {
  type = string
}

variable "resource_prefix" {
  type = string
}

variable "machine_type" {
  type = string
}

variable "disk_size_gb" {
  type = number
}

variable "subnet_self_link" {
  type = string
}

variable "ssh_username" {
  type = string
}

variable "ssh_public_key" {
  type      = string
  sensitive = true
}

variable "service_account_email" {
  type    = string
  default = null
}

variable "labels" {
  type    = map(string)
  default = {}
}
