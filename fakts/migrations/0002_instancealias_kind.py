# Generated by Django 5.2.1 on 2025-06-25 20:42

import django_choices_field.fields
import fakts.enums
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('fakts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='instancealias',
            name='kind',
            field=django_choices_field.fields.TextChoicesField(choices=[('absolute', 'ABSOLUTE (Value represent ABSOLUTE)'), ('relative', 'RELATIVE (Value represent RELATIVE)')], choices_enum=fakts.enums.AliasKindChoices, default='relative', help_text="The kind of alias. If relative, the alias is relative to the layer's domain. If absolute, the alias is an absolute URL.", max_length=8),
        ),
    ]
