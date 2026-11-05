# dev-wus2 environment: composes modules from ../../modules.
# Naming convention: <type>-opsagent-dev-wus2, e.g. rg-opsagent-dev-wus2.
#
# Placement: this lives in the shared Production subscription, isolated in its own resource
# group. Everything the project deploys goes in this group, so `terraform destroy` removes all
# of it and nothing else. The agent's Reader assignment (identity module) is a separate concern
# and is scoped to what it needs to read.

locals {
  name_suffix = "opsagent-dev-wus2"
  tags = {
    project    = "azure-ops-agent"
    env        = "dev"
    owner      = var.owner
    managed_by = "terraform"
  }
}

resource "azurerm_resource_group" "main" {
  name     = "rg-${local.name_suffix}"
  location = var.location
  tags     = local.tags
}

# TODO (weeks 3-4): network, identity, app, ai, monitoring modules into azurerm_resource_group.main.
