from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from fakts.models import App

# Create your models here.


class Structure(models.Model):
    identifier = models.CharField(
        max_length=1000,
        help_text="The identifier of the object. Consult the documentation for the format",
    )
    object = models.PositiveIntegerField(
        help_text="The object id of the object, on its associated service"
    )


class Room(models.Model):
    title = models.Model(max_length=1000, help_text="The Title of the Room")
    description = models.CharField(max_length=10000, null=True)
    creator = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, null=True, blank=True
    )
    pinned_by = models.ManyToManyField(
        get_user_model(),
        related_name="pinned_workspaces",
        blank=True,
        help_text="The users that have pinned the workspace",
    )


class Agent(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    name = models.CharField(max_length=10000, null=True)
    app = models.ForeignKey(App, max_length=4000)
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name="comments",
        help_text="The user that created this comment",
    )


class Message(models.Model):
    """
    Message represent the message of an agent on a room
    """

    attached_structures = models.ManyToManyField(Structure)
    targets = models.ManyToManyField(
        Agent,
        related_name="received_messages",
        help_text="The agents this message targets",
    )
    agent = models.ForeignKey(
        "Agent",
        on_delete=models.CASCADE,
        related_name="sent_message",
        help_text="The user that created this comment",
    )
    is_streaming = models.ForeignKey("Agent")
    text = models.TextField(help_text="A clear text representation of the rich comment")
    created_at = models.DateTimeField(
        auto_now_add=True, help_text="The time this comment got created"
    )
    is_reply_to = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="replies",
        help_text="Is This a reply to a certain comment",
    )
    descendants = models.JSONField(
        default=list,
        help_text="The immediate descendends of the comments. Think typed Rich Representation",
    )
    mentions = models.ManyToManyField(
        get_user_model(),
        blank=True,
        related_name="mentioned_in",
        help_text="The users that got mentioned in this comment",
    )
