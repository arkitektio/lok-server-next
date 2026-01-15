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

            
        print(django_repo.help("tailnets", "set-iam-policy"))
        print(django_repo.list_tailnets())
        
        for i in django_repo.list_tailnets():
            
            policy = {
                "subs": ["1","2","3","4","5"]
            }
            
            
            django_repo.update_policy(i.name, policy)
            
            
            print(i)
        
        
