from django.db import models

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


from django.contrib.auth import get_user_model
from django.db import models

# Create your models here.


class Comment(models.Model):
    """
    Comments represent the comments of a user on a specific data item 
    tart are identified by the unique combination of `identifier` and `object`.
    E.g a comment for an Image on the Mikro services would be serverd as
    `@mikro/image:imageID`. 

    Comments always belong to the user that created it. Comments in threads
    get a parent attribute set, that points to the immediate parent.

    Each comment contains multiple descendents, that make up a *rich* representation
    of the underlying comment data including potential mentions, or links, or 
    paragraphs.
    
    """


    identifier = models.CharField(max_length=1000, help_text="The identifier of the object. Consult the documentation for the format")
    object = models.PositiveIntegerField(help_text="The object id of the object, on its associated service")
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name="comments",
        help_text="The user that created this comment",
    )
    text = models.TextField(help_text="A clear text representation of the rich comment")
    created_at = models.DateTimeField(auto_now_add=True, help_text="The time this comment got created")
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="children", help_text="The parent of this comment. Think Thread"
    )
    descendants = models.JSONField(default=list, help_text="The immediate descendends of the comments. Think typed Rich Representation")
    mentions = models.ManyToManyField(
        get_user_model(), blank=True, related_name="mentioned_in", help_text="The users that got mentioned in this comment"
    )
    resolved = models.DateTimeField(null=True, blank=True, help_text="Is this comment marked as resolved?")
    resolved_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="resolved_comments",
        help_text="The user that resolved this comment"
    )

