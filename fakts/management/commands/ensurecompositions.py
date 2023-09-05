from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.conf import settings
import os
from fakts import models, base_models
import yaml

# import required module
from pathlib import Path


# assign directory
directory = "files"

# iterate over files in
# that directory


class Command(BaseCommand):
    help = "Creates an admin user non-interactively if it doesn't exist"

    def handle(self, *args, **kwargs):
        # Ensuring templates

        # iterate over files in
        # that directory
        templates = Path(settings.COMPOSITIONS_DIR).glob("*.yaml")
        for file in templates:
            filename = os.path.basename(file).split(".")[0]

            with open(file, "r") as file:
                template = file.read()

            validated = base_models.CompositionInputModel(template=template, name=filename)
            graph, _ = models.Composition.objects.update_or_create(
                name=validated.name, defaults=dict(template=validated.template)
            )
            print("Ensured template", filename)

       
