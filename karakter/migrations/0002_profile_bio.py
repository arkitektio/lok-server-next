# Generated by Django 4.2.5 on 2023-11-18 11:31

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("karakter", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="bio",
            field=models.CharField(blank=True, max_length=4000, null=True),
        ),
    ]
