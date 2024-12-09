import docker
import re
import socket


from fakts.backends.instances import registry
from fakts import models


def scan():
    registry.rescan()

    for service_description in registry.get_service_descriptors():

        service, created = models.Service.objects.update_or_create(
            identifier=service_description.identifier,
            defaults=dict(
                name=service_description.name or service_description.identifier,
                logo=service_description.logo,
                description=service_description.description,
            ),
        )

        print("Ensured service", service_description.identifier)

    for instance_description in registry.get_instance_descriptors():
        try:
            service = models.Service.objects.get(
                identifier=instance_description.service_identifier
            )
        except models.Service.DoesNotExist:
            print("Service", instance_description.service_identifier, "not found")
            raise

        instance, created = models.ServiceInstance.objects.update_or_create(
            identifier=instance_description.instance_identifier,
            backend=instance_description.backend_identifier,
            defaults=dict(service=service),
        )

        print("Ensured instance", instance_description.instance_identifier)

    return "token"
