# Generated by Django 4.2.5 on 2024-12-09 10:32

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("fakts", "0010_userdefinedserviceinstance"),
    ]

    operations = [
        migrations.AlterField(
            model_name="userdefinedserviceinstance",
            name="instance",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="defined",
                to="fakts.serviceinstance",
            ),
        ),
        migrations.AlterField(
            model_name="userdefinedserviceinstance",
            name="values",
            field=models.JSONField(default=list),
        ),
    ]
