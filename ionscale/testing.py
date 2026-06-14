"""In-memory ionscale repository for tests.

``FakeIonscaleRepository`` satisfies the :class:`ionscale.repo.IonscaleRepo`
protocol without touching the ``ionscale`` CLI or any network. It records the
calls made against it so tests can assert on them, and lets tests pre-seed the
data returned by read methods.

Install it either globally (via the ``IONSCALE_REPOSITORY`` setting, which the
test settings already point here) or per-test with
``ionscale.repo.set_ionscale_repo(FakeIonscaleRepository())``.
"""

from pathlib import Path
from typing import Any, Dict, List, Union

from .base_models import Machine, MachineDetail, Tailnet, TailnetCreate


class FakeIonscaleRepository:
    """Records calls and returns canned data; no subprocess, no binary."""

    def __init__(self) -> None:
        # Recorded calls — assert against these in tests.
        self.created_tailnets: List[TailnetCreate] = []
        self.updated_policies: List[tuple[str, Union[Dict[str, Any], str, Path]]] = []
        self.created_auth_keys: List[Dict[str, Any]] = []
        # Canned read data — seed these in tests as needed.
        self.machines_by_tailnet: Dict[str, List[Machine]] = {}
        self.machines: Dict[str, MachineDetail] = {}
        self.tailnets: List[Tailnet] = []
        self.auth_key: str = "tskey-fake-0000000000"

    def list_tailnets(self) -> List[Tailnet]:
        return list(self.tailnets)

    def list_machines(self, tailnet: str) -> List[Machine]:
        return list(self.machines_by_tailnet.get(tailnet, []))

    def get_machine(self, machine_id: str) -> MachineDetail:
        return self.machines[str(machine_id)]

    def create_tailnet(self, tailnet_input: TailnetCreate) -> Tailnet:
        self.created_tailnets.append(tailnet_input)
        tailnet = Tailnet(id=str(len(self.created_tailnets)), name=tailnet_input.name, dns_name=tailnet_input.name)
        self.tailnets.append(tailnet)
        return tailnet

    def update_policy(self, tailnet: str, policy: Union[Dict[str, Any], str, Path]) -> str:
        self.updated_policies.append((tailnet, policy))
        return "ok"

    def create_auth_key(self, tailnet: str, ephemeral: bool = False, pre_authorized: bool = True, tags: List[str] = None) -> str:
        self.created_auth_keys.append(
            {"tailnet": tailnet, "ephemeral": ephemeral, "pre_authorized": pre_authorized, "tags": tags or []}
        )
        return self.auth_key

    def run(self, *preargs) -> str:
        return ""

    def help(self, *preargs) -> str:
        return ""
