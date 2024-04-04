# Generated by Django 5.0.4 on 2024-04-04 14:08

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('matches', '0015_rename_matchmapban_mapban_and_more'),
        ('servers', '0004_remove_server_matches'),
    ]

    operations = [
        migrations.AddField(
            model_name='match',
            name='server',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='matches', to='servers.server'),
        ),
    ]
