import io
import json
import random
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.core.cache import cache
from matches.models import Match, MatchStatus
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.renderers import JSONRenderer

from matches.serializers import CreateMatchSerializer, KnifeRoundWinnerSerializer, MatchSerializer
from players.models import DiscordUser, Player
from players.serializers import PlayerSerializer

class MatchViewSet(viewsets.ModelViewSet):
    queryset = Match.objects.all()
    serializer_class = MatchSerializer

    def get_serializer_class(self):
        if self.action == 'list':
            return MatchSerializer
        if self.action == 'create':
            return CreateMatchSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer_class()(data=request.data)
        if serializer.is_valid():
            discord_users_ids = serializer.validated_data.get("discord_users_ids")
            print(discord_users_ids)
            if not discord_users_ids:
                return Response({"message": "Discord users cannot be empty"}, status=400)
            try:
                discord_users_list = [DiscordUser.objects.get(user_id=discord_user) for discord_user in discord_users_ids]
                players_list = [Player.objects.get(discord_user=discord_user) for discord_user in discord_users_list]

                for player in players_list:
                    if player.steam_user is None:
                        return Response({"message": f"Player {player.discord_user.username} has no connected steam account"}, status=400) 
                # create teams
                random.shuffle(players_list)

                # Split the list of members into two teams
                players_list_serialized = [PlayerSerializer(player) for player in players_list]
                players_list_json = [JSONRenderer().render(serializer.data) for serializer in players_list_serialized]
                num_members = len(players_list_serialized)
                middle_index = num_members // 2
                team1 = players_list_serialized[:middle_index]
                team2 =  players_list_serialized[middle_index:]
                team1_data = [serializer.data for serializer in team1]
                team2_data = [serializer.data for serializer in team2]

                team1_json = [JSONRenderer().render(serializer.data) for serializer in team1]
                team2_json = [JSONRenderer().render(serializer.data) for serializer in team2]

                # # Create a list of member names for each team
                # team1_names = [player.discord_user.username for player in team1]
                # team2_names = [player.discord_user.username for player in team2]

                # team1_steam_ids = [player.steam_user.steamid64 for player in team1]
                # team2_steam_ids = [player.steam_user.steamid64 for player in team2]

                match_data = {
                    "team1": team1_json,
                    "team2": team2_json,
                    "ct": "team1",
                    "t": "team2",
                    "players": players_list_json,
                    "status": MatchStatus.PENDING,
                    "knife_round": False,
                    "knife_team_winner": None,
                    "knife_team_winner_site": None,
                }
                json_render = JSONRenderer().render(match_data)
                print(json_render)
                cache.set("current_match", json_render, timeout=60*60*24*7)
                print(cache.get("current_match"))
                return Response(json_render, status=200)
            except DiscordUser.DoesNotExist as e:
                return Response({"message": f"Discord user {e} not exists"}, status=400)
            except Player.DoesNotExist as e:
                return Response({"message": f"Player {e} not exists"}, status=400)
        else:
            return Response(serializer.errors, status=400)
    @action(detail=False, methods=["GET"])
    def current(self, request):
        match_data = cache.get("current_match")
        if not match_data:
            return Response({"message": "No current match"}, status=404)
        return Response(json.loads(match_data), status=200)
    
    @action(detail=False, methods=["PUT"])
    def start_knife_round(self, request):
        match_data = cache.get("current_match")
        if not match_data:
            return Response({"message": "No current match"}, status=404)
        match_data = json.loads(match_data)
        match_data["knife_round"] = True
        cache.set("current_match", json.dumps(match_data), timeout=60*60*24*7)
        return Response({"message": "Knife round started"}, status=200)
    
    @action(detail=False, methods=["PUT"])
    def end_knife_round(self, request):
        serializer = KnifeRoundWinnerSerializer(data=request.data)
        if serializer.is_valid():
            match_data = cache.get("current_match")
            if not match_data:
                return Response({"message": "No current match"}, status=404)
            match_data = json.loads(match_data)
            match_data["knife_round"] = False
            match_data["knife_team_winner"] = "team1" if serializer.validated_data.get("winner") == "ct" else "team2"
            match_data["knife_team_winner_site"] = serializer.validated_data.get("site")
            if match_data["knife_team_winner"] == "team1" and match_data["knife_team_winner_site"] == "ct":
                match_data["ct"] = "team1"
                match_data["t"] = "team2"
            elif match_data["knife_team_winner"] == "team1" and match_data["knife_team_winner_site"] == "t":
                match_data["ct"] = "team2"
                match_data["t"] = "team1"
            elif match_data["knife_team_winner"] == "team2" and match_data["knife_team_winner_site"] == "ct":
                match_data["ct"] = "team2"
                match_data["t"] = "team1"
            elif match_data["knife_team_winner"] == "team2" and match_data["knife_team_winner_site"] == "t":
                match_data["ct"] = "team1"
                match_data["t"] = "team2"
            cache.set("current_match", json.dumps(match_data), timeout=60*60*24*7)
            return Response({"message": "Knife round ended"}, status=200)
        else:
            return Response(serializer.errors, status=400)

    @action(detail=False, methods=["PUT"])
    def start(self, request):
        match_data = cache.get("current_match")
        if not match_data:
            return Response({"message": "No current match"}, status=404)
        match_data = json.loads(match_data)
        match_data["status"] = MatchStatus.IN_PROGRESS
        cache.set("current_match", json.dumps(match_data), timeout=60*60*24*7)
        return Response({"message": "Match started"}, status=200)
    
    @action(detail=False, methods=["PUT"])
    def end(self, request):
        match_data = cache.get("current_match")
        if not match_data:
            return Response({"message": "No current match"}, status=404)
        match_data = json.loads(match_data)
        match_data["status"] = MatchStatus.FINISHED
        cache.set("current_match", json.dumps(match_data), timeout=60*60*24*7)
        return Response({"message": "Match ended"}, status=200)
    
    @action(detail=False, methods=["PUT"])
    def cancel(self, request):
        match_data = cache.get("current_match")
        if not match_data:
            return Response({"message": "No current match"}, status=404)
        match_data = json.loads(match_data)
        match_data["status"] = MatchStatus.CANCELLED
        cache.set("current_match", json.dumps(match_data), timeout=60*60*24*7)
        return Response({"message": "Match cancelled"}, status=200)
        
    # @action(detail=True, methods=["POST"])
    # def ban(self, request, pk=None):
    #     map_name = request.data.get("map_name")
    #     team = request.data.get("team")
    #     if not pk or not map_name:
    #         return Response({"message": "Invalid data."}, status=400)
    #     if not Match.objects.filter(id=pk).exists():
    #         return Response({"message": "Match not found."}, status=404)
    #     if not cache.get(f"match:{pk}"):
    #         return Response({"message": "Match not found."}, status=404)
    #     match_data = json.loads(cache.get(f"match:{pk}"))
    #     if map_name in match_data["banned_maps"]["ct"] or map_name in match_data["banned_maps"]["t"]:
    #         return Response({"message": "Map already banned."}, status=400)
    #     match_data["banned_maps"][team].append(map_name)
    #     match_data_cache = cache.set(f"match:{pk}", json.dumps(match_data), timeout=60*60*24*7)
    #     return Response({"message": "Map banned."}, status=200)
    
    # @action(detail=True, methods=["GET"])
    # def cache(self, request, pk=None):
    #     if not pk:
    #         return Response({"message": "Invalid data."}, status=400)
    #     if not Match.objects.filter(id=pk).exists():
    #         return Response({"message": "Match not found."}, status=404)
    #     if not cache.get(f"match:{pk}"):
    #         return Response({"message": "Match not found."}, status=404)
    #     match_data = json.loads(cache.get(f"match:{pk}"))
    #     return Response(match_data, status=200)

# @api_view(["POST"])
# def create_match(request):
#     # Create match logic

#     new_match = Match.objects.create(
#         status="pending",
#         type="competitive",
#         map="unknown",
#         winner="pending"
#     )
#     match_data = {
#         "banned_maps": [],
#     }
#     match_data_cache = cache.set(f"match:{new_match.id}", json.dumps(match_data), timeout=60*60*24*7)
#     print(cache.get(f"match:{new_match.id}"))
#     return Response({"message": "Match created."}, status=201)

# @api_view(["POST"])
# def ban_map(request):
#     # Ban map logic
#     match_id = request.data.get("match_id")
#     map_name = request.data.get("map_name")
#     if not match_id or not map_name:
#         return Response({"message": "Invalid data."}, status=400)
#     if not Match.objects.filter(id=match_id).exists():
#         return Response({"message": "Match not found."}, status=404)
#     if not cache.get(f"match:{match_id}"):
#         return Response({"message": "Match not found."}, status=404)
#     match_data = json.loads(cache.get(f"match:{match_id}"))
#     if map_name in match_data["banned_maps"]:
#         return Response({"message": "Map already banned."}, status=400)
#     match_data["banned_maps"].append(map_name)
#     match_data_cache = cache.set(f"match:{match_id}", json.dumps(match_data), timeout=60*60*24*7)
#     print(cache.get(f"match:{match_id}"))
#     return Response({"message": "Map banned."}, status=200)