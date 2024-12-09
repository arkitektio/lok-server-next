# Generated by Django 4.2.5 on 2024-12-09 13:28

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("fakts", "0011_alter_userdefinedserviceinstance_instance_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="userdefinedserviceinstance",
            name="instance",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="user_definitions",
                to="fakts.serviceinstance",
            ),
        ),
    ]
