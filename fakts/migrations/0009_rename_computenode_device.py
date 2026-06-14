# Rename ComputeNode -> Device and hash existing device ids per organization.

import django.db.models.deletion
from django.db import migrations, models

from karakter.hashers import hash_device_id


def hash_existing_node_ids(apps, schema_editor):
    """Replace stored raw device ids with their per-organization salted hash.

    Deterministic, so existing devices keep their grouping; the raw id stops
    existing on disk. Irreversible.
    """
    Device = apps.get_model('fakts', 'Device')
    for device in Device.objects.select_related('organization'):
        device.node_id = hash_device_id(device.node_id, device.organization)
        device.save(update_fields=['node_id'])


class Migration(migrations.Migration):

    dependencies = [
        ('fakts', '0008_client_role_devicecode_staging_role'),
        ('karakter', '0002_organization_device_salt'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='ComputeNode',
            new_name='Device',
        ),
        migrations.AlterField(
            model_name='device',
            name='organization',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='devices', to='karakter.organization'),
        ),
        migrations.AlterField(
            model_name='device',
            name='device_groups',
            field=models.ManyToManyField(blank=True, related_name='devices', to='fakts.devicegroup'),
        ),
        migrations.RunPython(hash_existing_node_ids, migrations.RunPython.noop),
    ]
