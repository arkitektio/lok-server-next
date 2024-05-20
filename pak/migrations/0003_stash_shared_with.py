# Generated by Django 4.2.5 on 2024-05-17 15:17

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("pak", "0002_stash_owner_alter_stashitem_stash"),
    ]

    operations = [
        migrations.AddField(
            model_name="stash",
            name="shared_with",
            field=models.ManyToManyField(
                related_name="shared_stashes", to=settings.AUTH_USER_MODEL
            ),
        ),
    ]