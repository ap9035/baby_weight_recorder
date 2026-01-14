# Serverless VPC Access Connector
# 讓 Cloud Run 服務可以透過 VPC 內網連接

resource "google_vpc_access_connector" "connector" {
  project       = var.project_id
  name          = "vpc-connector-${var.environment}"
  region        = var.region
  network       = var.vpc_network_name
  ip_cidr_range = var.ip_cidr_range

  machine_type = var.machine_type
  min_instances = var.min_instances
  max_instances = var.max_instances
}
