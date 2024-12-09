from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import StashItem
from pak.channels import stash_changed


@receiver(post_save, sender=StashItem)
def on_stash_changed(sender, instance, created, **kwargs):
    if created:
        stash_changed(
            {"stash_item_id": instance.id, "action": "create"}, [instance.stash.user]
        )
