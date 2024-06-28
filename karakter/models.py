import logging

import requests
from allauth.socialaccount.models import SocialAccount
from django.contrib.auth.models import AbstractUser, Group
from django.db import models

logger = logging.getLogger(__name__)


class User(AbstractUser):
    """A User of the System

    Lok Users are the main users of the system. They can be assigned to groups and have profiles, that can be used to display information about them.
    Each user is identifier by a unique username, and can have an email address associated with them.




    """

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
    """A Profile of a User"""

    name = models.CharField(max_length=1000, null=True, blank=True)
    bio = models.CharField(max_length=4000, null=True, blank=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    avatar = models.ImageField(null=True, blank=True)


class GroupProfile(models.Model):
    """A Profile of a Group"""

    name = models.CharField(max_length=1000, null=True, blank=True)
    group = models.OneToOneField(
        Group, on_delete=models.CASCADE, related_name="profile"
    )


class ComChannel(models.Model):
    """A Channel to send notifications to a user"""

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


class SystemMessage(models.Model):
    """A System Message"""

    hook = models.CharField(
        max_length=1000,
        null=True,
        blank=True,
        help_text="A hook that the ui can use to design the message",
    )
    title = models.CharField(max_length=1000, null=True, blank=True)
    message = models.CharField(max_length=4000, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="messages")
    created_at = models.DateTimeField(auto_now_add=True)
    action = models.CharField(help_text="The action to take (e.g. the node)")
    acknowledged = models.BooleanField(default=False)
    unique = models.CharField(max_length=1000, null=True, blank=True)


from .signals import *
