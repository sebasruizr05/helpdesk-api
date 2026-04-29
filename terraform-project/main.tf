locals {
  common_labels = merge(
    {
      environment = var.environment
      managed_by  = "terraform"
      project     = "helpdesk-api"
    },
    var.labels
  )
}
