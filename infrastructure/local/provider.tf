terraform {
  required_providers {
    vmworkstation = {
      source  = "elsudano/vmworkstation"
      version = "1.0.4"
    }
  }
}

provider "vmworkstation" {
  url      = var.vmrest_url
  user     = var.vmware_user
  password = var.vmware_password
  https    = false
  debug    = false
}