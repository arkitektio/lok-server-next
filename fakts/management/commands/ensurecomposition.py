import yaml
from django.core.management.base import BaseCommand
from fakts.models import Layer, Service, ServiceInstance, InstanceAlias
from fakts.config_models import YamlConfigModel  # <-- Your validated Pydantic schema
from django.contrib.auth import get_user_model
from django.conf import settings


User = get_user_model()


class Command(BaseCommand):
    help = "Import layers and service instances from YAML"

    def handle(self, *args, **options):
        layers = settings.FAKTS_LAYERS
        instances = settings.FAKTS_INSTANCES

        # Validate YAML structure
        config = YamlConfigModel(layers=layers, instances=instances)

        layer_lookup = {}

        # Create or update layers
        for layer in config.layers:
            obj, created = Layer.objects.update_or_create(
                identifier=layer.identifier,
                defaults={
                    "name": layer.name or layer.identifier,
                    "kind": layer.kind,
                    "description": layer.description,
                },
            )
            layer_lookup[layer.identifier] = obj
            self.stdout.write(self.style.SUCCESS(f"{'Created' if created else 'Updated'} layer: {obj.identifier}"))

        # Create or update services and instances
        for instance in config.instances:
            service, _ = Service.objects.get_or_create(identifier=instance.service, defaults={"name": instance.service})

            inst, created = ServiceInstance.objects.update_or_create(
                identifier=instance.identifier,
                defaults={
                    "steward": None,  # Optionally set to a default user
                    "service": service,
                },
            )
            self.stdout.write(self.style.SUCCESS(f"{'Created' if created else 'Updated'} instance: {inst.identifier}"))

            # Create aliases
            for alias in instance.aliases:
                layer = layer_lookup.get(alias.layer)
                if not layer:
                    self.stderr.write(self.style.ERROR(f"Layer '{alias.layer}' not found for alias '{alias.name}'"))
                    continue

                alias_obj, created_alias = InstanceAlias.objects.update_or_create(
                    instance=inst,
                    layer=layer,
                    name=alias.name,
                    defaults={
                        "host": alias.host,
                        "port": alias.port,
                        "ssl": alias.ssl,
                        "path": alias.path,
                        "kind": alias.kind,
                        "challenge": alias.challenge,
                    },
                )
                self.stdout.write(self.style.SUCCESS(f"{'Created' if created_alias else 'Updated'} alias: {alias_obj.name}"))
