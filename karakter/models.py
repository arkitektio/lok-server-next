import datetime
import logging
from typing import Optional, List, Tuple

import requests
from django.conf import settings
from django.contrib.auth.models import AbstractUser, Group
from django.db import models
from django.utils import timezone
import uuid
from karakter import fields, datalayer

logger = logging.getLogger(__name__)


class S3Store(models.Model):
    """Base model for objects stored in S3.

    Attributes mirror essential S3 metadata used elsewhere in the
    codebase.
    """

    path = fields.S3Field(null=True, blank=True, help_text="The stodre of the image", unique=True)
    key = models.CharField(max_length=1000)
    bucket = models.CharField(max_length=1000)
    populated = models.BooleanField(default=False)


class MediaStore(S3Store):
    """Small helper around S3-backed stored objects.

    Provides convenience helpers for generating presigned URLs and
    uploading content.
    """

    def get_presigned_url(self, info, datalayer: datalayer.Datalayer, host: Optional[str] = None) -> str:
        """Return a presigned URL for the stored S3 object.

        Args:
            info: GraphQL resolver info (passed through to datalayer if used).
            datalayer: object exposing ``s3`` boto3 session/client.
            host: optional host to replace the endpoint with when returning.
        """
        s3 = datalayer.s3
        url: str = s3.generate_presigned_url(
            ClientMethod="get_object",
            Params={
                "Bucket": self.bucket,
                "Key": self.key,
            },
            ExpiresIn=3600,
        )
        return url.replace(getattr(settings, "AWS_S3_ENDPOINT_URL", ""), host or "")

    def fill_info(self) -> None:
        """Populate or refresh derived metadata for the stored object."""
        pass

    def put_file(self, datalayer: datalayer.Datalayer, file) -> None:
        """Upload a file-like object to the object's S3 location and save model."""
        s3 = datalayer.s3
        s3.upload_fileobj(file, self.bucket, self.key)
        self.save()


class Organization(models.Model):
    """An Organization in the System

    An Organization is a group of users that can be used to manage access to resources.
    Each organization has a unique name and can have multiple users associated with it.
    """

    slug = models.CharField(max_length=1000, null=True, blank=True, unique=True)
    name = models.CharField(max_length=1000, null=True, blank=True)
    description = models.CharField(max_length=4000, null=True, blank=True)
    avatar = models.ForeignKey(MediaStore, on_delete=models.CASCADE, null=True)
    owner = models.ForeignKey("User", on_delete=models.CASCADE, related_name="owned_organizations")

    def __str__(self):
        return self.name or self.slug or "Unnamed Organization"


class Role(models.Model):
    identifier = models.CharField(max_length=1000, null=True, blank=True)
    description = models.CharField(max_length=4000, null=True, blank=True)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="roles")
    creating_instance = models.ForeignKey("fakts.ServiceInstance", on_delete=models.CASCADE, null=True, blank=True)
    is_builtin = models.BooleanField(default=False, help_text="If this role is a built-in role that cannot be deleted (admin)")

    class Meta:
        unique_together = ("identifier", "organization")


class Scope(models.Model):
    identifier = models.CharField(max_length=1000, null=True, blank=True)
    description = models.CharField(max_length=4000, null=True, blank=True)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="scopes")
    creating_instance = models.ForeignKey("fakts.ServiceInstance", on_delete=models.CASCADE, null=True, blank=True)
    is_builtin = models.BooleanField(default=False, help_text="If this scope is a built-in scope that cannot be deleted (admin)")

    class Meta:
        unique_together = ("identifier", "organization")


class Membership(models.Model):
    """A Membership of a User in an Organization with a Role"""

    user = models.ForeignKey("User", on_delete=models.CASCADE, related_name="memberships")
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="memberships")
    roles = models.ManyToManyField(Role, related_name="memberships", blank=True)

    class Meta:
        unique_together = ("user", "organization")


class User(AbstractUser):
    """A User of the System

    Lok Users are the main users of the system. They can be assigned to groups and have profiles, that can be used to display information about them.
    Each user is identifier by a unique username, and can have an email address associated with them.


    """

    email = models.EmailField(null=True, blank=True)
    active_organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="active_users",
        null=True,
        blank=True,
        help_text="The organization that the user is currently active in",
    )

    @property
    def is_faktsadmin(self):
        return self.groups.filter(name="admin").exists()

    @property
    def avatar(self):
        return None

    def notify(self, title: str, message: str) -> List[Tuple[Optional[int], str]]:
        """Send a notification to all registered communication channels.

        Logs publish failures but attempts all channels. Returns a list of
        (channel_id, status) tuples so callers can inspect individual
        delivery results.
        """
        results: List[Tuple[Optional[int], str]] = []
        for channel in self.com_channels.all():
            try:
                status = channel.publish(title, message)
            except Exception:
                logger.exception("Error publishing to channel=%s for user=%s", getattr(channel, "id", None), getattr(self, "id", None))
                status = "Error"
            results.append((getattr(channel, "id", None), status))

        return results


class Profile(models.Model):
    """A Profile of a User"""

    name = models.CharField(max_length=1000, null=True, blank=True)
    bio = models.CharField(max_length=4000, null=True, blank=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    avatar = models.ForeignKey(MediaStore, on_delete=models.CASCADE, null=True)
    banner = models.ForeignKey(MediaStore, on_delete=models.CASCADE, null=True, related_name="profile_banners")


class OrganizationProfile(models.Model):
    """A Profile of a User"""

    name = models.CharField(max_length=1000, null=True, blank=True)
    bio = models.CharField(max_length=4000, null=True, blank=True)
    organization = models.OneToOneField(Organization, on_delete=models.CASCADE, related_name="profile")
    avatar = models.ForeignKey(MediaStore, on_delete=models.CASCADE, null=True)
    banner = models.ForeignKey(MediaStore, on_delete=models.CASCADE, null=True, related_name="organization_banners")


class GroupProfile(models.Model):
    """A Profile of a Group"""

    name = models.CharField(max_length=1000, null=True, blank=True)
    group = models.OneToOneField(Group, on_delete=models.CASCADE, related_name="profile")
    bio = models.CharField(max_length=4000, null=True, blank=True)
    avatar = models.ForeignKey(MediaStore, on_delete=models.CASCADE, null=True)


class ComChannel(models.Model):
    """A Channel to send notifications to a user"""

    name = models.CharField(max_length=1000, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="com_channels")
    token = models.CharField(max_length=1000, null=True, blank=True, unique=True)

    def publish(self, title: str, message: str) -> str:
        """Publish a notification to the configured push endpoint.

        Returns a string status and logs HTTP/JSON errors instead of
        raising to make caller handling simpler.
        """
        try:
            resp = requests.post(
                "https://exp.host/--/api/v2/push/send",
                json={
                    "to": self.token,
                    "title": title,
                    "body": message,
                },
                timeout=5,
            )
            resp.raise_for_status()
        except requests.RequestException:
            logger.exception("HTTP error while publishing to token=%s", self.token)
            return "Error"

        try:
            data = resp.json()
            # Safely navigate nested JSON
            status = data.get("data", {}).get("status", "unknown")
            return status
        except ValueError:
            logger.exception("Invalid JSON response when publishing to token=%s", self.token)
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


class Invite(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        DECLINED = "declined", "Declined"
        CANCELLED = "cancelled", "Cancelled"

    token = models.UUIDField(default=uuid.uuid4, unique=True, db_index=True)
    email = models.EmailField(null=True, blank=True)  # Optional, for reference only
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="created_invites")
    created_for = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="invites")
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    # Status tracking
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    accepted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="accepted_invites")
    declined_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="declined_invites")
    responded_at = models.DateTimeField(null=True, blank=True)

    # Roles to assign when invite is accepted
    roles = models.ManyToManyField("Role", related_name="invites", blank=True)

    def is_valid(self):
        if self.status != self.Status.PENDING:
            return False
        if self.expires_at and self.expires_at < timezone.now():
            return False
        return True

    def accept(self, user):
        self.status = self.Status.ACCEPTED
        self.accepted_by = user
        self.responded_at = timezone.now()
        self.save(update_fields=["status", "accepted_by", "responded_at"])

    def decline(self, user):
        self.status = self.Status.DECLINED
        self.declined_by = user
        self.responded_at = timezone.now()
        self.save(update_fields=["status", "declined_by", "responded_at"])

    def cancel(self):
        self.status = self.Status.CANCELLED
        self.save(update_fields=["status"])


from .signals import *
