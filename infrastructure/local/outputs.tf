output "vm_ids" {
  value = { for k, v in vmworkstation_vm.vm : k => v.id }
}