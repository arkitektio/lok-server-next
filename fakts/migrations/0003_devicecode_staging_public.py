# Generated by Django 4.2.5 on 2024-01-05 20:52

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("fakts", "0002_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="devicecode",
            name="staging_public",
            field=models.BooleanField(default=False),
        ),
    ]