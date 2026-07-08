from django.db import migrations, models


class Migration(migrations.Migration):
    """Rename KommunityPartner.preconfigured_composition -> preconfigured_hub.

    Hand-written as a RenameField (the autodetector proposed a data-losing
    remove+add). The `pre_authorize_hook` AlterField only updates help_text (no DB
    change) so state stays in sync.
    """

    dependencies = [
        ("fakts", "0008_rename_composition_to_hub"),
    ]

    operations = [
        migrations.RenameField(
            model_name="kommunitypartner",
            old_name="preconfigured_composition",
            new_name="preconfigured_hub",
        ),
        migrations.AlterField(
            model_name="kommunitypartner",
            name="preconfigured_hub",
            field=models.JSONField(
                blank=True,
                null=True,
                help_text="A preconfigured hub that gets created when a user redeems a token from this partner.",
            ),
        ),
        migrations.AlterField(
            model_name="kommunitypartner",
            name="pre_authorize_hook",
            field=models.CharField(
                blank=True,
                null=True,
                max_length=1000,
                help_text="Optional hook called after creating a partner hub. The response must explicitly approve the hub.",
            ),
        ),
    ]
