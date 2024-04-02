# Generated by Django 4.2.5 on 2024-04-02 10:30

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("fakts", "0007_alter_devicecode_staging_kind_redeemtoken"),
    ]

    operations = [
        migrations.AlterField(
            model_name="redeemtoken",
            name="client",
            field=models.OneToOneField(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="redeemed_client",
                to="fakts.client",
            ),
        ),
    ]
