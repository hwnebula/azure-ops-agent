"""Azure credential resolution.

In Azure, the app runs as a user-assigned managed identity (its client ID is in
``AZURE_CLIENT_ID``) with Reader only. Locally, DefaultAzureCredential falls back to the
developer's ``az login``. Interactive browser login is disabled so nothing ever prompts
inside a server.
"""

from __future__ import annotations

import os
from functools import lru_cache

from azure.core.credentials import TokenCredential
from azure.identity import DefaultAzureCredential


@lru_cache(maxsize=1)
def get_credential() -> TokenCredential:
    return DefaultAzureCredential(
        managed_identity_client_id=os.environ.get("AZURE_CLIENT_ID") or None,
        exclude_interactive_browser_credential=True,
    )
