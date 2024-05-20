# Generated by Django 4.2.5 on 2024-04-01 08:49

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("fakts", "0005_serviceinstancemapping_description"),
    ]

    operations = [
        migrations.AlterField(
            model_name="release",
            name="requirements",
            field=models.JSONField(default=dict),
        ),
        migrations.CreateModel(
            name="InstanceConfig",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("key", models.CharField(max_length=1000)),
                ("value", models.JSONField(default=dict)),
                (
                    "instance",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="configs",
                        to="fakts.serviceinstance",
                    ),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="instanceconfig",
            constraint=models.UniqueConstraint(
                fields=("instance", "key"), name="Only one config per instance and key"
            ),
        ),
    ]