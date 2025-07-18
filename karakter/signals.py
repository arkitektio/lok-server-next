from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db.models.signals import post_save
from django.dispatch import receiver
from allauth.account.signals import user_signed_up
from .models import Profile, Organization, Role
from django.core.mail import send_mail
import logging

logger = logging.getLogger(__name__)
User = get_user_model()



def create_role(organization: Organization, identifier: str):
    """
    Create a role for the organization with the given identifier.
    """
    group_name = f"{organization.slug}:{identifier}"
    group, _ = Group.objects.get_or_create(name=group_name)
    role, _ = Role.objects.update_or_create(
        identifier=identifier,
        organization=organization,
        defaults={"group": group}
    )
    return role

def create_default_groups_for_org(org: Organization):
    for identifier in ["admin", "guest", "user", "bot", "viewer", "editor", "contributor", "manager", "owner", "labeler"]:
        create_role(org, identifier)
        
        
def ensure_admins_are_admins_for_org(org: Organization):
    """
    Ensure that the admin user is added to the admin group of the organization.
    """
    User = get_user_model()
    admin_users = User.objects.filter(is_superuser=True).all()
    for user in admin_users:
        role = create_role(org, "admin")
        user.groups.add(role.group)
        user.save()



@receiver(post_save, sender=Organization)
def ensure_default_groups_for_org(sender, instance, created, **kwargs):
    create_default_groups_for_org(instance)
    ensure_admins_are_admins_for_org(instance)




@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
        instance.profile.save()

        for i in settings.SYSTEM_MESSAGES:
            instance.notify(i["title"], i["message"])


@receiver(user_signed_up)
def user_signed_up_handler(request, user, **kwargs):
    user.is_active = False
    user.save()


@receiver(post_save, sender=User)
def notify_user_activation(sender, instance, created, **kwargs):
    if not created and instance.is_active:
        # Only send if previously inactive
        try:
            send_mail(
                "Your account has been approved",
                "You can now log in.",
                "no-reply@example.com",
                [instance.email],
            )
        except Exception as e:
            logger.error("Failed to send activation email", exc_info=True)
            # Handle the error as needed, e.g., log it or notify admins
