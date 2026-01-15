from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.conf import settings
from karakter.base_models import UserConfig
from karakter.models import Organization, User, Role, Membership
from ionscale.repo import django_repo
from ionscale.base_models import TailnetCreate




class Command(BaseCommand):
    help = "Creates all lok user non-interactively if it doesn't exist"

    def handle(self, *args, **kwargs):
        
        #print(django_repo.create_tailnet(TailnetCreate(name="test-tailnet",)))

            
        print(django_repo.run("machines", "get", "--machine-id", "196503777216299015" ))
        raise
        print(django_repo.list_tailnets())
        
        for t in django_repo.list_tailnets():
            print(f"Machines in tailnet {t.name}:")
            machines = django_repo.list_machines(t.name)
            for m in machines:
                print(f" - {m.name} (id: {m.id}, ipv4: {m.ipv4}, ipv6: {m.ipv6})")
        
        
        
