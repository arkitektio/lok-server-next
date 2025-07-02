from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from allauth.account.signals import user_signed_up
from .models import Profile
from django.core.mail import send_mail
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


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
