# Generated by Django 4.2.5 on 2025-03-18 17:49

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("karakter", "0002_groupprofile_bio"),
        ("fakts", "0002_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="client",
            name="logo",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="karakter.mediastore",
            ),
        ),
    ]
