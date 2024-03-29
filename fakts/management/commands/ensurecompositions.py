from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.conf import settings
import os
from fakts import models, base_models
import yaml

from fakts.backends.instances import registry


# import required module
from pathlib import Path


# assign directory
directory = "files"

# iterate over files in
# that directory


class Command(BaseCommand):
    help = "Creates an admin user non-interactively if it doesn't exist"

    def handle(self, *args, **kwargs):
            

            for service_description in registry.get_service_descriptors():
                
                service, created = models.Service.objects.update_or_create(
                    identifier=service_description.identifier, defaults=dict(name=service_description.name or service_description.identifier, logo=service_description.logo, description=service_description.description)
                )

                print("Ensured service", service_description.identifier)

            for instance_description in registry.get_instance_descriptors():
                try:
                    service = models.Service.objects.get(identifier=instance_description.service_identifier)
                except models.Service.DoesNotExist:
                    print("Service", instance_description.service_identifier, "not found")
                    raise

                instance, created = models.ServiceInstance.objects.update_or_create(
                    identifier=instance_description.instance_identifier, backend=instance_description.backend_identifier, defaults=dict(service=service)
                )

                print("Ensured instance", instance_description.instance_identifier)

            for composition_description in registry.get_composition_descriptors():
                graph, created = models.Composition.objects.update_or_create(
                    name=composition_description.name
                )
                
                print("Ensured Composition", composition_description.name)

                for key, instance_map in composition_description.services.items():
                    try:
                        instance = models.ServiceInstance.objects.get(identifier=instance_map.instance_identifier, backend=instance_map.backend_identifier)
                    except models.ServiceInstance.DoesNotExist:
                        print("Service", instance_map.instance_identifier, "not found on backend", instance_map.backend_identifier)
                        raise

                    mapping, created = models.ServiceInstanceMapping.objects.update_or_create(
                        key=key, composition=graph, defaults=dict(instance=instance)
                    )

                    print("Ensured mapping", mapping, key, "to", instance)



                     


                
                 


       
