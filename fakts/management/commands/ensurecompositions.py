from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.conf import settings
import os
from fakts import models, base_models
import yaml
from fakts.scan import scan
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

        scan()
        



                     


                
                 


       
