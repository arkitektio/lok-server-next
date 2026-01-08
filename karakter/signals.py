from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db.models.signals import post_save
from django.dispatch import receiver
from allauth.account.signals import user_signed_up
from .models import Profile, Organization, Role, OrganizationProfile, Membership
from django.core.mail import send_mail
import logging
from karakter import managers

logger = logging.getLogger(__name__)
User = get_user_model()


@receiver(post_save, sender=Organization)
def ensure_default_roles_for_org(sender, instance, created, **kwargs):
    managers.create_default_roles_for_org(instance)
    managers.ensure_owner_is_admin(instance)
    managers.create_default_scopes_for_org(instance)
    if created:
        OrganizationProfile.objects.create(organization=instance)


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
        instance.profile.save()

        for i in settings.SYSTEM_MESSAGES:
            instance.notify(i["title"], i["message"])


@receiver(post_save, sender=User)
def create_user_default_organization(sender, instance, created, **kwargs):
    if created:
        managers.create_user_default_organization(instance)


@receiver(user_signed_up)
def user_signed_up_handler(request, user, **kwargs):
    # Automatically sets the user to inactive until approved
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
