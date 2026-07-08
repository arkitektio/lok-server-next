import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    """Rename Composition -> Hub (and CompositionDeviceCode -> HubDeviceCode).

    Hand-written because the `related_name` changes on Hub's own FKs defeat the
    autodetector's field-rename heuristic. All operations are metadata renames /
    constraint recreations — data is preserved (tables/columns are renamed in place).
    """

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("fakts", "0007_meshdevicecode"),
    ]

    operations = [
        # 1. Models -> tables fakts_hub / fakts_hubdevicecode
        migrations.RenameModel(old_name="Composition", new_name="Hub"),
        migrations.RenameModel(old_name="CompositionDeviceCode", new_name="HubDeviceCode"),
        # 2. Drop every constraint that references the `composition` field BEFORE the
        #    rename (sqlite remakes tables and would otherwise emit SQL for a column
        #    that no longer exists). Constraint NAME changes are also handled here.
        migrations.RemoveConstraint(model_name="hub", name="Only one composition identifier per organization"),
        migrations.RemoveConstraint(model_name="serviceinstance", name="Only one token per composition"),
        migrations.RemoveConstraint(model_name="serviceinstance", name="Only one instance_id per release, organization and device and instance"),
        migrations.RemoveConstraint(model_name="serviceinstancemapping", name="Only one instance per key and composition"),
        # 3. FK columns composition_id -> hub_id on every referencing model
        migrations.RenameField(model_name="client", old_name="composition", new_name="hub"),
        migrations.RenameField(model_name="ionscaleauthkey", old_name="composition", new_name="hub"),
        migrations.RenameField(model_name="serviceinstance", old_name="composition", new_name="hub"),
        migrations.RenameField(model_name="redeemtoken", old_name="composition", new_name="hub"),
        migrations.RenameField(model_name="hubdevicecode", old_name="composition", new_name="hub"),
        # 4. related_name changes on Hub's own FKs (no DB change; keep state in sync)
        migrations.AlterField(
            model_name="hub",
            name="organization",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="hubs",
                to="karakter.organization",
            ),
        ),
        migrations.AlterField(
            model_name="hub",
            name="creator",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="created_hubs",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="hub",
            name="auth_key",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="hubs",
                to="fakts.ionscaleauthkey",
            ),
        ),
        # 5. Recreate the constraints against the renamed `hub` field / new names.
        migrations.AddConstraint(
            model_name="hub",
            constraint=models.UniqueConstraint(
                fields=("organization", "identifier"),
                name="Only one hub identifier per organization",
            ),
        ),
        migrations.AddConstraint(
            model_name="serviceinstance",
            constraint=models.UniqueConstraint(
                fields=("token", "hub"),
                name="Only one token per hub",
            ),
        ),
        migrations.AddConstraint(
            model_name="serviceinstance",
            constraint=models.UniqueConstraint(
                fields=("release", "instance_id", "organization", "device", "hub"),
                name="Only one instance_id per release, organization and device and instance",
            ),
        ),
        migrations.AddConstraint(
            model_name="serviceinstancemapping",
            constraint=models.UniqueConstraint(
                fields=("key", "client"),
                name="Only one instance per key and hub",
            ),
        ),
    ]
