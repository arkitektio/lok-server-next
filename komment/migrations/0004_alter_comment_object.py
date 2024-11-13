# Generated by Django 4.2.5 on 2024-11-13 11:27

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("komment", "0003_alter_comment_created_at_alter_comment_descendants_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="comment",
            name="object",
            field=models.CharField(
                help_text="The object id of the object, on its associated service",
                max_length=1000,
            ),
        ),
    ]
