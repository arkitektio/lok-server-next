from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class TailnetCreate(BaseModel):
    name: str = Field(..., description="The unique name of the tailnet")
    # Add other create-time options here if needed (e.g., OIDC settings)


class DNSConfig(BaseModel):
    """The per-tailnet DNS configuration pushed via `ionscale tailnets set-dns`.

    Mirrors ionscale's ``ionscale.v1.DNSConfig``. Note that ``set-dns`` *replaces*
    the whole config on every call (the CLI uses presence-based flags), so callers
    must send the full desired state — lok is the source of truth. The MagicDNS
    suffix is server-configured (``dns.magic_dns_suffix``) and has no CLI flag.
    """

    magic_dns: bool = False
    https_certs: bool = False
    override_local_dns: bool = False
    nameservers: List[str] = Field(default_factory=list)
    search_domains: List[str] = Field(default_factory=list)


class Tailnet(BaseModel):
    id: str
    name: str
    dns_name: Optional[str] = None
    created_at: Optional[datetime] = None

    # Use ConfigDict for Pydantic v2, or class Config for v1
    model_config = {"from_attributes": True}


class TailnetList(BaseModel):
    tailnets: List[Tailnet]


class Machine(BaseModel):
    id: str
    name: str
    tailnet: Optional[str] = None
    ipv4: Optional[str] = None
    ipv6: Optional[str] = None
    ephemeral: bool = False
    connected: bool = False
    last_seen: Optional[datetime] = None
    tags: List[str] = Field(default_factory=list)
    # `ionscale machines list` reports AUTHORIZED, so it's reliably available. None = unknown.
    authorized: Optional[bool] = None

    model_config = {"from_attributes": True}

class MachineDetail(Machine):
    os: Optional[str] = None
    key_expiry: Optional[datetime] = None
    # None means "not reported by the CLI" (unknown) — distinct from a known False. Not sourced
    # from the CLI yet, so it stays None rather than a misleading False.
    is_external: Optional[bool] = None
    fqdn: Optional[str] = None  # The machine's MagicDNS name, if present in the CLI output.

    # Add other fields as needed based on `ionscale machines get` output


class MachineList(BaseModel):
    machines: List[Machine]
