# Generated by Django 5.0.2 on 2024-02-21 14:55

import django.db.models.deletion
import prefix_id.field
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('matches', '0001_initial'),
        ('players', '0003_team'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='match',
            name='map',
        ),
        migrations.RemoveField(
            model_name='match',
            name='players',
        ),
        migrations.RemoveField(
            model_name='match',
            name='winner',
        ),
        migrations.AddField(
            model_name='match',
            name='maps',
            field=models.CharField(choices=[('de_mirage', 'Mirage'), ('de_inferno', 'Inferno'), ('de_nuke', 'Nuke'), ('de_vertigo', 'Vertigo'), ('de_overpass', 'Overpass'), ('de_ancient', 'Ancient'), ('de_anubis', 'Anubus')], default='de_mirage', max_length=255),
        ),
        migrations.AlterField(
            model_name='match',
            name='status',
            field=models.CharField(choices=[('PENDING', 'Pending'), ('IN_PROGRESS', 'In Progress'), ('FINISHED', 'Finished'), ('CANCELED', 'Canceled')], default='PENDING', max_length=255),
        ),
        migrations.AlterField(
            model_name='match',
            name='type',
            field=models.CharField(choices=[('BO1', 'Bo1'), ('BO2', 'Bo2'), ('BO3', 'Bo3'), ('BO5', 'Bo5')], default='BO1', max_length=255),
        ),
        migrations.AlterField(
            model_name='matchplayer',
            name='player',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='matches_players', to='players.player'),
        ),
        migrations.AlterField(
            model_name='matchplayer',
            name='team',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='players.team'),
        ),
        migrations.CreateModel(
            name='MatchTeam',
            fields=[
                ('id', prefix_id.field.PrefixIDField(editable=False, max_length=33, prefix='match_team', primary_key=True, serialize=False, unique=True)),
                ('side', models.CharField(blank=True, choices=[('CT', 'Ct'), ('T', 'T')], max_length=255, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('match', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='matches.match')),
                ('team', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='players.team')),
            ],
        ),
        migrations.AddField(
            model_name='match',
            name='teams',
            field=models.ManyToManyField(related_name='matches', through='matches.MatchTeam', to='players.team'),
        ),
    ]
