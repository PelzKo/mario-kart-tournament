from django.contrib import admin
from .models import Tournament, Player, GroupGame, GroupGameParticipant, CupVote, BracketGame, BracketParticipant

admin.site.register(Tournament)
admin.site.register(Player)
admin.site.register(GroupGame)
admin.site.register(GroupGameParticipant)
admin.site.register(CupVote)
admin.site.register(BracketGame)
admin.site.register(BracketParticipant)
