import math

from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Q
from django.db.models.signals import post_save
from django.dispatch import receiver
from prefix_id import PrefixIDField

from players.models import Team, Player

UserModel = get_user_model()


class MatchStatus(models.TextChoices):
    CREATED = "CREATED"
    STARTED = "STARTED"
    LOADED = "LOADED"
    LIVE = "LIVE"
    FINISHED = "FINISHED"
    CANCELLED = "CANCELLED"


class MatchType(models.TextChoices):
    BO1 = "BO1"
    BO3 = "BO3"
    BO5 = "BO5"


class GameMode(models.TextChoices):
    COMPETITIVE = "COMPETITIVE"
    WINGMAN = "WINGMAN"
    AIM = "AIM"


class Map(models.Model):
    id = PrefixIDField(primary_key=True, prefix="map")
    name = models.CharField(max_length=255, unique=True)
    tag = models.CharField(max_length=255, unique=True)
    guild = models.ForeignKey("guilds.Guild", on_delete=models.CASCADE, related_name="maps", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"<{self.name} - {self.tag}>"


class MapPool(models.Model):
    id = PrefixIDField(primary_key=True, prefix="map_pool")
    name = models.CharField(max_length=255, unique=True)
    maps = models.ManyToManyField(Map, related_name="map_pools")
    guild = models.ForeignKey("guilds.Guild", on_delete=models.CASCADE, related_name="map_pools", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name if not self.guild else f"<{self.name} - {self.guild.name}>"


class MapBan(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="map_bans")
    map = models.ForeignKey(Map, on_delete=models.CASCADE, related_name="map_bans")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"<{self.team.name} - {self.map.name}>"


class MapPick(models.Model):
    team = models.ForeignKey(
        Team, on_delete=models.CASCADE, related_name="map_selected"
    )
    map = models.ForeignKey(Map, on_delete=models.CASCADE, related_name="map_picks")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"<{self.team.name} - {self.map.name}>"


class MatchConfig(models.Model):
    id = PrefixIDField(primary_key=True, prefix="match_config")
    name = models.CharField(max_length=255, unique=True)
    game_mode = models.CharField(
        max_length=255, choices=GameMode.choices, default=GameMode.COMPETITIVE
    )
    type = models.CharField(
        max_length=255, choices=MatchType.choices, default=MatchType.BO1
    )
    map_pool = models.ForeignKey(MapPool, on_delete=models.CASCADE, related_name="match_configs", null=True, blank=True)
    map_sides = models.JSONField(null=True, blank=True)
    clinch_series = models.BooleanField(default=False)
    max_players = models.PositiveIntegerField(default=10)
    cvars = models.JSONField(null=True, blank=True)
    guild = models.ForeignKey("guilds.Guild", on_delete=models.CASCADE, related_name="match_configs", null=True, blank=True)
    shuffle_teams = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class MatchManager(models.Manager):

    def check_server_is_available_for_match(self, server):
        return not self.filter(
            Q(server=server) &
            (Q(status=MatchStatus.LIVE) | Q(status=MatchStatus.STARTED))
        ).exists()


# Create your models here.
class Match(models.Model):
    objects = MatchManager()

    status = models.CharField(
        max_length=255, choices=MatchStatus.choices, default=MatchStatus.CREATED
    )
    config = models.ForeignKey(MatchConfig, on_delete=models.CASCADE, related_name="matches", null=True, blank=True)
    team1 = models.ForeignKey(
        Team, on_delete=models.CASCADE, related_name="matches_team1", null=True, blank=True
    )
    team2 = models.ForeignKey(
        Team, on_delete=models.CASCADE, related_name="matches_team2", null=True, blank=True
    )
    winner_team = models.ForeignKey(
        Team, on_delete=models.CASCADE, related_name="matches_winner", null=True, blank=True
    )
    map_bans = models.ManyToManyField(MapBan, related_name="matches_map_bans", blank=True)
    map_picks = models.ManyToManyField(
        MapPick, related_name="matches_map_picks", blank=True
    )
    last_map_ban = models.ForeignKey(MapBan, on_delete=models.CASCADE, related_name="matches_last_map_ban", null=True, blank=True)
    last_map_pick = models.ForeignKey(MapPick, on_delete=models.CASCADE, related_name="matches_last_map_pick",
                                      null=True, blank=True)
    maplist = models.JSONField(null=True, blank=True)
    cvars = models.JSONField(null=True, blank=True)
    message_id = models.CharField(max_length=255, null=True, blank=True)
    author = models.ForeignKey("players.DiscordUser", on_delete=models.CASCADE, related_name="matches", null=True)
    server = models.ForeignKey(
        "servers.Server", on_delete=models.CASCADE, related_name="matches", null=True, blank=True
    )
    guild = models.ForeignKey("guilds.Guild", on_delete=models.CASCADE, related_name="matches", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def api_key_header(self):
        return "Authorization"

    @property
    def load_match_command_name(self):
        return "matchzy_loadmatch_url"

    def __str__(self):
        return f"<{self.status} - {self.config.name} - {self.pk}>"

    def get_team1_players_dict(self):
        return {
            "name": self.team1.name,
            "players": self.team1.get_players_dict(),
        }

    def get_team2_players_dict(self):
        return {
            "name": self.team2.name,
            "players": self.team2.get_players_dict(),
        }

    def get_matchzy_config(self):
        num_maps = 1 if self.config.type == MatchType.BO1 else 3
        players_count = self.team1.players.count() + self.team2.players.count()
        players_per_team = players_count / 2
        players_per_team_rounded = math.ceil(players_per_team)
        matchzy_config = {
            "matchid": self.pk,
            "team1": self.get_team1_players_dict(),
            "team2": self.get_team2_players_dict(),
            "num_maps": num_maps,
            "maplist": self.maplist,
            "map_sides": self.config.map_sides,
            "clinch_series": self.config.clinch_series,
            "players_per_team": players_per_team_rounded,
        }
        if self.cvars:
            config_cvars = self.config.cvars
            if config_cvars:
                self.cvars.update(config_cvars)
            matchzy_config["cvars"] = self.cvars
        if self.config.game_mode == GameMode.WINGMAN:
            matchzy_config["wingman"] = True
        return matchzy_config

    def get_connect_command(self):
        return "" if not self.server else self.server.get_connect_string()

    def get_author_token(self):
        return UserModel.objects.get(player__discord_user=self.author).get_token()

    def create_webhook_cvars(self, webhook_url: str):
        self.cvars = self.cvars or {}
        self.cvars.update({
            "matchzy_remote_log_url": webhook_url,
            "matchzy_remote_log_header_key": self.api_key_header,
            "matchzy_remote_log_header_value": f"Bearer {self.get_author_token()}",
        })
        self.save()

    def ban_map(self, team, map):
        map_ban = MapBan.objects.create(team=team, map=map)
        self.map_bans.add(map_ban)
        self.last_map_ban = map_ban

        if self.config.type == MatchType.BO1:
            # 6 bans
            map_bans_count = self.map_bans.objects.count()
            # 7 maps
            map_pool_count = self.config.map_pool.maps.count() - 1
            if map_bans_count == map_pool_count:
                # Select the last map
                map_to_select = self.config.map_pool.maps.exclude(map_bans__match=self).first()
                self.maplist.append(map_to_select.tag)
        elif self.config.type == MatchType.BO3:
            # 4 bans
            map_bans_count = self.map_bans.objects.count()
            # 7 maps
            map_pool_count = self.config.map_pool.maps.count() - 3
            if map_bans_count == map_pool_count:
                map_to_select = self.config.map_pool.maps.exclude(map_bans__match=self).first()
                self.maplist.append(map_to_select.tag)

        self.save()
        return self

    def pick_map(self, team, map):
        map_pick = MapPick.objects.create(team=team, map=map)
        self.map_picks.add(map_pick)
        # add map to maplist without removing it
        self.maplist.append(map.tag)
        self.last_map_pick = map_pick
        self.save()
        return self

    def shuffle_players(self):
        players_list = list(self.team1.players.all()) + list(self.team2.players.all())
        players_count = len(players_list)
        middle_index = players_count // 2
        team1_players = players_list[:middle_index]
        team2_players = players_list[middle_index:]
        self.team1.players.set(team1_players)
        self.team1.leader = team1_players[0]
        self.team2.players.set(team2_players)
        self.team2.leader = team2_players[0]
        self.save()

    def change_teams_name(self):
        self.team1.name = f"team_{self.team1.leader.steam_user.username}"
        self.team1.save()
        self.team2.name = f"team_{self.team2.leader.steam_user.username}"
        self.team2.save()

    def add_player_to_match(self, player):
        if self.team1.players.count() < self.team2.players.count():
            self.team1.players.add(player)
        elif self.team2.players.count() < self.team1.players.count():
            self.team2.players.add(player)
        else:
            self.team1.players.add(player)
        self.save()
        return self

    def remove_player_from_match(self, player):
        if player in self.team1.players.all():
            self.team1.players.remove(player)
        elif player in self.team2.players.all():
            self.team2.players.remove(player)
        self.save()
        return self

    def start_match(self):
        self.status = MatchStatus.STARTED
        if self.config.shuffle_teams:
            self.shuffle_players()
        self.change_teams_name()
        self.save()
        return self



@receiver(post_save, sender=Match)
def match_post_save(sender, instance, created, **kwargs):
    if created:
        team1_player = Player.objects.get(discord_user=instance.author)
        team1 = Team.objects.create(name="Team 1")
        team1.players.add(team1_player)
        team1.save()
        team2 = Team.objects.create(name="Team 2")

        instance.team1 = team1
        instance.team2 = team2
        instance.save()
