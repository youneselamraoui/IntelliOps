locals {
  vms = {
    "vm-staging"    = { desc = "Serveur applicatif Staging",    cpu = 2, ram = 4096 }
    "vm-prod"       = { desc = "Serveur applicatif Production", cpu = 2, ram = 4096 }
    "vm-staging-db" = { desc = "Serveur PostgreSQL Staging",    cpu = 2, ram = 1024 }
    "vm-prod-db"    = { desc = "Serveur PostgreSQL Production", cpu = 2, ram = 1024 }
  }
}

resource "vmworkstation_vm" "vm" {
  for_each     = local.vms
  denomination = each.key
  description  = each.value.desc
  processors   = each.value.cpu
  memory       = each.value.ram
  sourceid     = var.source_vm_id
  path         = "${var.vm_dir}\\${each.key}\\${each.key}.vmx"

  lifecycle {
    ignore_changes = [description]
  }
}