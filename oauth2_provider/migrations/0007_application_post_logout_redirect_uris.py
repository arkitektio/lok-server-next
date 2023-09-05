# Generated by Django 4.1.5 on 2023-01-14 12:32

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("oauth2_provider", "0006_alter_application_client_secret"),
    ]

    operations = [
        migrations.AddField(
            model_name="application",
            name="post_logout_redirect_uris",
            field=models.TextField(
                blank=True, help_text="Allowed Post Logout URIs list, space separated"
            ),
        ),
    ]