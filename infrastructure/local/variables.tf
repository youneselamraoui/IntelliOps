variable "vmrest_url" {
  type    = string
  default = "http://127.0.0.1:8697/api"
}

variable "vmware_user" {
  type    = string
  default = "younes"
}

variable "vmware_password" {
  type      = string
  sensitive = true
}

variable "source_vm_id" {
  description = "ID API de infra_base"
  type        = string
  default     = "NQ4SHJ0U264VDPM0EG6IHGJ998GM74VU"
}

variable "vm_dir" {
  type    = string
  default = "C:\\VMs\\infra"
}