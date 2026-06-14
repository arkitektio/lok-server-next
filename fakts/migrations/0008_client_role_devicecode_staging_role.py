import django_choices_field.fields
from django.db import migrations

import fakts.enums


class Migration(migrations.Migration):

    dependencies = [
        ("fakts", "0007_add_client_statuses"),
    ]

    operations = [
        migrations.AddField(
            model_name="client",
            name="role",
            field=django_choices_field.fields.TextChoicesField(
                choices=[
                    ("interface", "INTERFACE (Value represent INTERFACE)"),
                    ("agent", "AGENT (Value represent AGENT)"),
                ],
                choices_enum=fakts.enums.ClientRoleChoices,
                default="interface",
                help_text="Operational role: human INTERFACE vs autonomous task-receiving AGENT.",
                max_length=9,
            ),
        ),
        migrations.AddField(
            model_name="devicecode",
            name="staging_role",
            field=django_choices_field.fields.TextChoicesField(
                choices=[
                    ("interface", "INTERFACE (Value represent INTERFACE)"),
                    ("agent", "AGENT (Value represent AGENT)"),
                ],
                choices_enum=fakts.enums.ClientRoleChoices,
                default="interface",
                help_text="The operational role of the staging client (INTERFACE vs AGENT)",
                max_length=9,
            ),
        ),
    ]
