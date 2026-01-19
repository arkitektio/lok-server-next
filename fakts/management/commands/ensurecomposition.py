import yaml
from django.core.management.base import BaseCommand
from fakts.models import Layer, Service, ServiceInstance, InstanceAlias, ServiceRelease, Composition
from karakter.models import Organization, Role, Scope
from fakts.config_models import YamlConfigModel  # <-- Your validated Pydantic schema
from django.contrib.auth import get_user_model
from django.conf import settings
import uuid


User = get_user_model()


class Command(BaseCommand):
    help = "Import layers, service instances and compositions from YAML"

    def handle(self, *args, **options):
        compositions_config = settings.FAKTS_COMPOSITIONS

        # Validate YAML structure
        config = YamlConfigModel(compositions=compositions_config)

        layer_lookup = {}

        # Ensure Default Org
        default_org = Organization.objects.first()
        if not default_org:
            default_org = Organization.objects.create(name="Arkitekt", slug="arkitekt")
            self.stdout.write(self.style.WARNING(f"Created default organization: {default_org}"))

        # Ensure Steward
        steward = User.objects.filter(is_superuser=True).first()
        if not steward:
            steward = User.objects.filter(is_staff=True).first()

        if not steward:
            steward = User.objects.first()

        if not steward:
            self.stdout.write(self.style.ERROR("No users found. Creating a default superuser 'admin'."))
            steward = User.objects.create_superuser("admin", "admin@example.com", "admin")

        def ensure_instance(instance, composition):
            service, _ = Service.objects.get_or_create(identifier=instance.service, defaults={"name": instance.service})

            release, _ = ServiceRelease.objects.get_or_create(service=service, version=instance.version)

            if instance.organization:
                instance_org = Organization.objects.filter(slug=instance.organization).first() or Organization.objects.filter(name=instance.organization).first() or default_org
            elif composition:
                instance_org = composition.organization

            inst, created = ServiceInstance.objects.update_or_create(
                token=instance.identifier,
                defaults={
                    "steward": steward,
                    "release": release,
                    "organization": instance_org,
                    "template": "{}",
                    "instance_id": instance.identifier,
                    "composition": composition,
                },
            )
            self.stdout.write(self.style.SUCCESS(f"{'Created' if created else 'Updated'} instance: {inst.token}"))

            # Create/Update Roles
            for role_config in instance.roles:
                role, created_role = Role.objects.get_or_create(organization=instance_org, identifier=role_config.identifier, defaults={"description": role_config.description, "creating_instance": inst})
                if not created_role and role_config.description:
                    role.description = role_config.description
                    role.save()

                role.used_by.add(inst)
                self.stdout.write(self.style.SUCCESS(f"{'Created' if created_role else 'Updated'} role: {role.identifier}"))

            # Create/Update Scopes
            for scope_config in instance.scopes:
                scope, created_scope = Scope.objects.get_or_create(organization=instance_org, identifier=scope_config.identifier, defaults={"description": scope_config.description, "creating_instance": inst})
                if not created_scope and scope_config.description:
                    scope.description = scope_config.description
                    scope.save()

                scope.used_by.add(inst)
                self.stdout.write(self.style.SUCCESS(f"{'Created' if created_scope else 'Updated'} scope: {scope.identifier}"))

            # Create aliases
            for alias in instance.aliases:
                alias_obj, created_alias = InstanceAlias.objects.update_or_create(
                    instance=inst,
                    name=alias.name,
                    defaults={
                        "host": alias.host,
                        "port": alias.port,
                        "ssl": alias.ssl if alias.ssl is not None else True,  # Default to True if not specified
                        "path": alias.path,
                        "kind": alias.kind,
                        "challenge": alias.challenge,
                    },
                )
                self.stdout.write(self.style.SUCCESS(f"{'Created' if created_alias else 'Updated'} alias: {alias_obj.name}"))

        # Create Compositions
        for comp_config in config.compositions:
            try:
                comp_org = Organization.objects.get(slug=comp_config.organization)
            except Organization.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Organization {comp_config.organization} not found for composition {comp_config.name}. Please ensure it is created first."))
                continue

            identifier = comp_config.identifier or comp_config.name  # fallback to name

            try:
                # Check if UUID
                uuid.UUID(identifier)
                token = identifier
            except ValueError:
                # Generate deterministic UUID from identifier if it is not a UUID
                token = str(uuid.uuid5(uuid.NAMESPACE_DNS, identifier))

            comp, created = Composition.objects.update_or_create(token=token, defaults={"name": comp_config.name, "description": comp_config.description, "organization": comp_org, "creator": steward})
            self.stdout.write(self.style.SUCCESS(f"{'Created' if created else 'Updated'} composition: {comp.name}"))

            for instance in comp_config.instances:
                ensure_instance(instance, composition=comp)
