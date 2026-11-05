"""Curated Resource Graph queries for common ops and security questions.

The agent should use these first. They are reviewed, return stable shapes the evals can score
against, and take only typed, validated parameters. Model-written KQL is a fallback (see
``resource_graph.ResourceGraphQueryInput``).

Each template uses ``string.Template`` placeholders. String parameters are inserted as escaped
KQL literals, and integers as plain digits.
"""

from __future__ import annotations

from dataclasses import dataclass
from string import Template
from typing import Any, Literal, get_args

from pydantic import BaseModel, ConfigDict, Field

from tools.kql import kql_string


class _Params(BaseModel):
    model_config = ConfigDict(extra="forbid")


class NoParams(_Params):
    pass


class TagParams(_Params):
    tag_name: str = Field(
        pattern=r"^[A-Za-z0-9 _.:\-]{1,128}$", description="Tag key to check, e.g. 'owner'."
    )


class ResourceTypeParams(_Params):
    resource_type: str = Field(
        pattern=r"^[A-Za-z0-9.]+(/[A-Za-z0-9]+)+$",
        description="ARM resource type, e.g. 'microsoft.compute/virtualmachines'.",
    )


class HoursParams(_Params):
    hours: int = Field(
        default=24, ge=1, le=336, description="Look-back window in hours (max 14 days)."
    )


@dataclass(frozen=True)
class NamedQuery:
    name: str
    description: str
    template: Template
    params_model: type[_Params] = NoParams

    def render(self, parameters: dict[str, Any] | None = None) -> str:
        params = self.params_model.model_validate(parameters or {})
        substitutions = {
            key: kql_string(value) if isinstance(value, str) else str(int(value))
            for key, value in params.model_dump().items()
        }
        return self.template.substitute(substitutions).strip()


NamedQueryName = Literal[
    "public_storage_accounts",
    "public_ip_addresses",
    "nsg_rules_open_to_internet",
    "resource_count_by_type",
    "resources_by_type",
    "resources_missing_tag",
    "recent_changes",
]

_QUERIES = [
    NamedQuery(
        name="public_storage_accounts",
        description=(
            "Storage accounts reachable from the public internet: network access is open to "
            "all networks (public network access not Disabled and firewall default action "
            "Allow), or anonymous blob access is allowed."
        ),
        template=Template("""
resources
| where type =~ 'microsoft.storage/storageaccounts'
| extend publicNetworkAccess = tostring(properties.publicNetworkAccess),
         defaultAction = tostring(properties.networkAcls.defaultAction),
         allowBlobPublicAccess = tobool(properties.allowBlobPublicAccess)
| extend networkOpenToAll = publicNetworkAccess !~ 'Disabled' and defaultAction =~ 'Allow',
         anonymousBlobAccess = allowBlobPublicAccess == true
| where networkOpenToAll or anonymousBlobAccess
| project id, name, resourceGroup, subscriptionId, location, publicNetworkAccess,
          defaultAction, allowBlobPublicAccess, networkOpenToAll, anonymousBlobAccess
| order by name asc
"""),
    ),
    NamedQuery(
        name="public_ip_addresses",
        description="Public IP addresses, with their allocation method and attached resource.",
        template=Template("""
resources
| where type =~ 'microsoft.network/publicipaddresses'
| extend ipAddress = tostring(properties.ipAddress),
         allocationMethod = tostring(properties.publicIPAllocationMethod),
         attachedTo = tostring(properties.ipConfiguration.id)
| project id, name, resourceGroup, subscriptionId, location, ipAddress, allocationMethod,
          attachedTo
| order by name asc
"""),
    ),
    NamedQuery(
        name="nsg_rules_open_to_internet",
        description=(
            "Inbound Allow NSG rules whose source is any address (*, 0.0.0.0/0, Internet, Any)."
        ),
        template=Template("""
resources
| where type =~ 'microsoft.network/networksecuritygroups'
| mv-expand rule = properties.securityRules
| extend direction = tostring(rule.properties.direction),
         access = tostring(rule.properties.access),
         sourcePrefix = tostring(rule.properties.sourceAddressPrefix),
         sourcePrefixes = tostring(rule.properties.sourceAddressPrefixes)
| where direction =~ 'Inbound' and access =~ 'Allow'
| where sourcePrefix in~ ('*', '0.0.0.0/0', 'Internet', 'Any')
     or sourcePrefixes contains '"*"' or sourcePrefixes contains '0.0.0.0/0'
     or sourcePrefixes contains '"Internet"'
| project id, nsgName = name, resourceGroup, subscriptionId,
          ruleName = tostring(rule.name), priority = toint(rule.properties.priority),
          protocol = tostring(rule.properties.protocol), sourcePrefix, sourcePrefixes,
          destinationPortRange = tostring(rule.properties.destinationPortRange),
          destinationPortRanges = tostring(rule.properties.destinationPortRanges)
| order by nsgName asc, priority asc
"""),
    ),
    NamedQuery(
        name="resource_count_by_type",
        description="Count of resources per resource type, largest first.",
        template=Template("""
resources
| summarize resourceCount = count() by type
| order by resourceCount desc
"""),
    ),
    NamedQuery(
        name="resources_by_type",
        description="All resources of one ARM resource type.",
        template=Template("""
resources
| where type =~ $resource_type
| project id, name, type, resourceGroup, subscriptionId, location, tags
| order by name asc
"""),
        params_model=ResourceTypeParams,
    ),
    NamedQuery(
        name="resources_missing_tag",
        description="Resources that lack a given tag key or have an empty value for it.",
        template=Template("""
resources
| where isempty(tostring(tags[$tag_name]))
| project id, name, type, resourceGroup, subscriptionId, location
| order by type asc, name asc
"""),
        params_model=TagParams,
    ),
    NamedQuery(
        name="recent_changes",
        description=(
            "Resource changes (create, update, delete) recorded by Resource Graph change "
            "tracking in the last N hours, newest first. Includes who made each change and "
            "with which client."
        ),
        template=Template("""
resourcechanges
| extend changeTime = todatetime(properties.changeAttributes.timestamp),
         targetResourceId = tostring(properties.targetResourceId),
         changeType = tostring(properties.changeType),
         changedBy = tostring(properties.changeAttributes.changedBy),
         clientType = tostring(properties.changeAttributes.clientType),
         operation = tostring(properties.changeAttributes.operation)
| where changeTime > ago(${hours}h)
| project id, changeTime, targetResourceId, changeType, changedBy, clientType, operation
| order by changeTime desc
"""),
        params_model=HoursParams,
    ),
]

NAMED_QUERIES: dict[str, NamedQuery] = {q.name: q for q in _QUERIES}

if set(NAMED_QUERIES) != set(get_args(NamedQueryName)):  # pragma: no cover - import-time guard
    raise RuntimeError("NamedQueryName is out of sync with NAMED_QUERIES")


def describe_named_queries() -> str:
    lines = []
    for q in _QUERIES:
        fields = q.params_model.model_fields
        params = ", ".join(
            f"{n} ({f.annotation.__name__ if f.annotation else 'any'})" for n, f in fields.items()
        )
        lines.append(f"- {q.name}: {q.description}" + (f" Parameters: {params}." if params else ""))
    return "\n".join(lines)
