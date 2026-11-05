variable "subscription_id" {
  description = "Subscription that hosts the project's resource group (and that the agent reads)."
  type        = string
}

variable "location" {
  description = "Azure region."
  type        = string
  default     = "westus2"
}

variable "owner" {
  description = "Owner tag value."
  type        = string
  default     = "Harold Williams"
}
