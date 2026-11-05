terraform {
  required_version = ">= 1.9"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
  }
  # Local state for now. Moves to an azurerm backend (OIDC auth) when the deploy pipeline lands.
}

# Auth: Azure CLI locally; in GitHub Actions set ARM_USE_OIDC=true and ARM_CLIENT_ID/ARM_TENANT_ID.
provider "azurerm" {
  features {}
  subscription_id = var.subscription_id
}
