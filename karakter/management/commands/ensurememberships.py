from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.conf import settings
from karakter.base_models import UserConfig
from karakter.models import Organization, Role, Membership

User = get_user_model()

class Command(BaseCommand):
    help = "Creates all memberships based on user config"

    def handle(self, *args, **kwargs):
        lokusers = settings.ENSURED_USERS

        for lokuser in lokusers:
            try:
                user_config = UserConfig(**lokuser)

                user = User.objects.filter(username=user_config.username).first()
                if not user:
                    self.stdout.write(self.style.WARNING(f"User {user_config.username} not found. Skipping memberships."))
                    continue

                # Clear existing memberships ?? Maybe only update/create, but clear might be safer for "ensure"
                # Membership.objects.filter(user=user).delete() 
                # Better to update/create or just add. If we delete, we lose manual changes.
                # However, ensure usually implies strict state. The previous code did delete.
                # Let's keep deletion for now to match previous behavior but scoped.
                
                # Check if we should clear. If config has memberships, maybe we want to enforce ONLY those? 
                
                for membershipc in user_config.memberships:
                    try:
                        org = Organization.objects.get(slug=membershipc.organization)
                    except Organization.DoesNotExist:
                        self.stdout.write(self.style.ERROR(f"Organization {membershipc.organization} not found for user {user.username}"))
                        continue

                    membership, created = Membership.objects.update_or_create(
                        user=user,
                        organization=org,
                    )
                    
                    if created:
                         self.stdout.write(self.style.SUCCESS(f"Created membership {user.username} -> {org.slug}"))
                    else:
                         self.stdout.write(f"Updated membership {user.username} -> {org.slug}")

                    current_roles = set()
                    for role_identifier in membershipc.roles:
                        try:
                            role = Role.objects.get(organization=org, identifier=role_identifier)
                            membership.roles.add(role)
                            current_roles.add(role)
                            
                            # Also add to group
                            group_name = f"{org.slug}:{role.identifier}"
                            group, _ = Group.objects.get_or_create(name=group_name)
                            user.groups.add(group)
                            
                        except Role.DoesNotExist:
                             self.stdout.write(self.style.ERROR(f"Role {role_identifier} not found in org {org.slug}"))
                    
                    user.save()
                    membership.save()
            
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error processing memberships for {lokuser}: {e}"))


                    membership.save()

                print(f"Added membershipts {user_config.memberships} to user {user.username}")
            except Exception as e:
                self.stderr.write(f"Error creating/updating user {lokuser}: {e}")
