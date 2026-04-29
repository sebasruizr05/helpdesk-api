variable "project_id" {
  type = string
}

variable "region" {
  type = string
}

variable "resource_prefix" {
  type = string
}

variable "network_cidr" {
  type = string
}

variable "private_service_cidr" {
  type = string
}

variable "ssh_source_ranges" {
  type = list(string)
}

variable "labels" {
  type    = map(string)
  default = {}
}
