import docker
import re
import socket


from fakts.backends.instances import registry
from fakts import models



def scan():
    registry.rescan()


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

    return "token"





    