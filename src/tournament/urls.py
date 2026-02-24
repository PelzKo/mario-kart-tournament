"""URL patterns for the tournament app."""
from django.urls import path

from . import views

app_name = "tournament"

urlpatterns = [
    # Landing / create
    path("", views.create_tournament, name="create"),
    path("tournament/created/<str:admin_token>/", views.tournament_created, name="created"),

    # Viewer (read-only)
    path("tournament/<str:viewer_token>/", views.viewer, name="viewer"),

    # Admin / organizer
    path("tournament/<str:admin_token>/admin/", views.admin_dashboard, name="admin_dashboard"),
    path("tournament/<str:admin_token>/admin/bracket/generate/", views.generate_bracket, name="generate_bracket"),
    path("tournament/<str:admin_token>/bracket/", views.bracket_view, name="bracket_view"),

    # Group stage actions
    path("tournament/<str:admin_token>/game/<int:game_id>/vote/", views.vote_cup, name="vote_cup"),
    path("tournament/<str:admin_token>/game/<int:game_id>/results/", views.group_results, name="group_results"),

    # Bracket actions
    path("tournament/<str:admin_token>/bracket/<int:game_id>/results/", views.bracket_results, name="bracket_results"),
]
