output "network_self_link" {
  value = google_compute_network.vpc.self_link
}

output "subnet_self_link" {
  value = google_compute_subnetwork.subnet.self_link
}

output "network_name" {
  value = google_compute_network.vpc.name
}

output "private_service_connection" {
  value = google_service_networking_connection.private_vpc_connection.id
}
