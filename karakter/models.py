from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import Group
import requests
import logging
from allauth.socialaccount.models import SocialAccount
logger = logging.getLogger(__name__)


class User(AbstractUser):
    """A reflection on the real User"""

    email = models.EmailField(null=True, blank=True)


    @property
    def is_faktsadmin(self):
        return self.groups.filter(name="admin").exists()

    @property
    def avatar(self):
        if self.profile:
            return self.profile.avatar.url if self.profile.avatar else None

    def notify(self, title, message):
        for channel in self.channels.all():
            channel.publish(title, message)


class Profile(models.Model):
    name = models.CharField(max_length=1000, null=True, blank=True)
    bio = models.CharField(max_length=4000, null=True, blank=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")


class GroupProfile(models.Model):
    name = models.CharField(max_length=1000, null=True, blank=True)
    group = models.OneToOneField(
        Group, on_delete=models.CASCADE, related_name="profile"
    )


class ComChannel(models.Model):
    name = models.CharField(max_length=1000, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="channels")
    token = models.CharField(max_length=1000, null=True, blank=True, unique=True)

    def publish(self, title, message):
        try:
            x = requests.post(
                "https://exp.host/--/api/v2/push/send",
                json={
                    "to": self.token,
                    "title": title,
                    "body": message,
                },
            )
            status = x.json()["data"]["status"]
            return status
        except Exception as e:
            logger.error("Publish error", exc_info=True)
            return "Error"


from .signals import *