# Generated by Django 4.2.5 on 2023-11-20 15:52

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("karakter", "0002_profile_bio"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="avatar",
            field=models.ImageField(blank=True, null=True, upload_to=""),
        ),
    ]
