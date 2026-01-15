import subprocess
import os
import shutil
import re
import json
from typing import List, Dict, Any, Union
from pathlib import Path
from .base_models import Tailnet, TailnetCreate, Machine, MachineDetail
from django.conf import settings


class IonscaleRepository:
    def __init__(self, server_url: str, admin_key: str, binary_path: str = "ionscale"):
        """
        Initializes the repository.
        :param server_url: The full URL of your Ionscale instance (e.g. https://vpn.corp.com)
        :param admin_key: The System Admin Key
        :param binary_path: Path to ionscale binary (default: lookup in PATH)
        """
        self.server_url = server_url
        self.admin_key = admin_key

        # Verify binary exists
        self.binary = shutil.which(binary_path)
        if not self.binary:
            raise FileNotFoundError(f"Ionscale binary not found at: {binary_path}")

    def _run_command(self, args: List[str], command_type: str = "tailnet") -> str:
        """
        Executes the ionscale CLI command securely.
        :param args: Command arguments
        :param command_type: The command type (e.g. 'tailnet', 'iam')
        """
        # We inject the key as an env var to avoid it showing up in process lists,
        # assuming the CLI can read it or we pass it via stdin.
        # Ionscale CLI requires the flag, so we pass it in the args but execute carefully.

        base_cmd = [self.binary,  *args]

        try:
            result = subprocess.run(
                base_cmd,
                capture_output=True,
                text=True,
                check=True,
                # We can inject extra env vars if needed
                env={
                    "IONSCALE_SYSTEM_ADMIN_KEY": self.admin_key,
                    "IONSCALE_ADDR": self.server_url,
                },
            )
            return result.stdout.strip()

        except subprocess.CalledProcessError as e:
            # Clean the error message to avoid leaking keys if they appear in stderr
            clean_error = e.stderr.replace(self.admin_key, "***")
            raise RuntimeError(f"Ionscale CLI Error: {clean_error}")

    def list_tailnets(self) -> List[Tailnet]:
        """
        Runs `ionscale tailnet list` and parses the output.
        """
        output = self._run_command(["tailnet", "list"])
        print(output)
        return self._parse_list_output(output)

    def list_machines(self, tailnet: str) -> List[Machine]:
        """
        Runs `ionscale machines list --tailnet <tailnet>` and parses the output.
        """
        output = self._run_command(["machines", "list", "--tailnet", tailnet])
        return self._parse_machine_list_output(output)

    def get_machine(self, machine_id: str) -> MachineDetail:
        """
        Runs `ionscale machines get --machine-id <machine_id>` and parses the output.
        """
        output = self._run_command(["machines", "get", "--machine-id", machine_id])
        return self._parse_machine_detail_output(output)

    def create_tailnet(self, tailnet_input: TailnetCreate) -> Tailnet:
        """
        Runs `ionscale tailnet create` and returns the created object.
        """
        # Ionscale create usually returns "Tailnet created: {id}" or similar
        self._run_command(["tailnet", "create", "--name", tailnet_input.name])

        # Since create command output might be sparse, we fetch the specific tailnet
        # to return a full object. This is a "read-your-writes" pattern.
        # Alternatively, you can just return a basic object.

        # Optimization: Just return the known data if you want speed
        return Tailnet(
            id="unknown",  # ID is generated server side, would need lookup
            name=tailnet_input.name,
            dns_name=f"{tailnet_input.name}.{self.server_url.split('://')[1]}",
        )

    def update_policy(self, tailnet: str, policy: Union[Dict[str, Any], str, Path]) -> str:
        """
        Updates the policy for a tailnet.

        :param tailnet: The name of the tailnet
        :param policy: Policy data as a dict, JSON string, or path to a JSON file
        :return: CLI output message

        Example:
            # Using a dictionary
            repo.update_policy("my-tailnet", {"acls": [...]})

            # Using a file path
            repo.update_policy("my-tailnet", "/path/to/policy.json")

            # Using a JSON string
            repo.update_policy("my-tailnet", '{"acls": [...]}')
        """
        import tempfile

        # Determine if we need to create a temporary file
        if isinstance(policy, dict):
            # Convert dict to JSON and write to temp file
            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
                json.dump(policy, f, indent=2)
                temp_file = f.name

            try:
                output = self._run_command(["tailnets", "set-iam-policy", "--tailnet", tailnet, "--file", temp_file], command_type="iam")
                return output
            finally:
                # Clean up temp file
                os.unlink(temp_file)

        elif isinstance(policy, (str, Path)):
            # Check if it's a file path
            policy_path = Path(policy)
            if policy_path.exists():
                # It's a file path
                output = self._run_command(["tailnets", "set-iam-policy", "--tailnet", tailnet, "--file", str(policy_path)], command_type="iam")
                return output
            else:
                # Assume it's a JSON string, write to temp file
                with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
                    f.write(policy)
                    temp_file = f.name

                try:
                    output = self._run_command(["update-policy", "--tailnet", tailnet, "--file", temp_file], command_type="iam")
                    return output
                finally:
                    # Clean up temp file
                    os.unlink(temp_file)
        else:
            raise ValueError("policy must be a dict, JSON string, or file path")

    def _parse_list_output(self, cli_output: str) -> List[Tailnet]:
        """
        Parses the ASCII table output from Ionscale into Pydantic models.

        Expected CLI Output format (example):
        ID    NAME        DNS_NAME
        1     marketing   marketing.vpn.com
        2     dev         dev.vpn.com
        """
        lines = cli_output.splitlines()
        tailnets = []

        # Skip header line (ID, NAME, etc)
        if not lines:
            return []

        # Flexible parsing: Split by whitespace
        # You might need to adjust this based on exact CLI version output
        for line in lines[1:]:
            parts = line.split()
            if len(parts) >= 2:
                # Basic mapping based on typical column order
                # Adjust index based on your actual CLI output columns
                t_id = parts[0]
                name = parts[1]

                # Check if dns_name exists in columns
                dns_name = parts[2] if len(parts) > 2 else None

                tailnets.append(Tailnet(id=t_id, name=name, dns_name=dns_name))

        return tailnets

    def _parse_machine_list_output(self, cli_output: str) -> List[Machine]:
        """
        Parses the ASCII table output from Ionscale into Pydantic models.
        """
        lines = cli_output.splitlines()
        machines = []

        # Skip header line
        if not lines:
            return []

        for line in lines[1:]:
            parts = line.split()
            if len(parts) >= 2:
                m_id = parts[0]
                name = parts[1]
                
                # Heuristic mapping
                ipv4 = parts[2] if len(parts) > 2 else None
                ipv6 = parts[3] if len(parts) > 3 else None
                
                connected = False
                if "true" in line.lower():
                    connected = True
                    
                machines.append(Machine(
                    id=m_id, 
                    name=name,
                    ipv4=ipv4,
                    ipv6=ipv6,
                    connected=connected
                ))

        return machines

    def _parse_machine_detail_output(self, cli_output: str) -> MachineDetail:
        """
        Parses the output from `ionscale machines get` into a MachineDetail model.
        Supports both "Key: Value" and column-aligned formats.
        """
        lines = cli_output.splitlines()
        data = {}
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Try splitting by 2 or more spaces first (column format)
            parts = re.split(r'\s{2,}', line)
            if len(parts) >= 2:
                key = parts[0].strip().lower().replace(" ", "_")
                value = parts[1].strip()
                data[key] = value
                continue
                
            # Fallback to colon separation
            if ":" in line:
                key, value = line.split(":", 1)
                data[key.strip().lower().replace(" ", "_")] = value.strip()

        return MachineDetail(
            id=data.get("id", ""),
            name=data.get("machine_name", data.get("name", "")),
            tailnet=data.get("tailnet"),
            ipv4=data.get("tailscale_ipv4", data.get("ipv4")),
            ipv6=data.get("tailscale_ipv6", data.get("ipv6")),
            connected=False, # Not present in detail view usually
            ephemeral=data.get("ephemeral", "false").lower() == "true",
            last_seen=None, # "a few seconds ago" is not easily parsable to datetime without logic
            os=data.get("os"),
            key_expiry=None, # "in 6 months"
            authorized=False, # Not explicitly in sample
            is_external=False, # Not explicitly in sample
        )
    
    def run(self, *preargs) -> str:
        """
        Runs arbitrary ionscale CLI commands.
        """
        output = self._run_command(list(preargs), command_type="")
        return output
    
    def help(self, *preargs) -> str:
        """
        Returns the help text of the ionscale CLI.
        """
        output = self._run_command(list(preargs) + ["--help"], command_type="")
        return output


django_repo = IonscaleRepository(
    server_url=settings.IONSCALE_SERVER_URL,
    admin_key=settings.IONSCALE_ADMIN_KEY,
)
