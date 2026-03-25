"""URL patterns for the tournament app."""
from django.urls import path

from . import views

app_name = "tournament"

urlpatterns = [
    # Landing / list
    path("", views.tournament_list, name="list"),
    # Create
    path("new/", views.create_tournament, name="create"),
    path("tournament/created/<str:admin_token>/", views.tournament_created, name="created"),

    # Viewer (read-only)
    path("tournament/<str:viewer_token>/", views.viewer, name="viewer"),

    # Admin / organizer
    path("tournament/<str:admin_token>/admin/login/", views.admin_login, name="admin_login"),
    path("tournament/<str:admin_token>/admin/", views.admin_dashboard, name="admin_dashboard"),
    path("tournament/<str:admin_token>/admin/bracket/generate/", views.generate_bracket, name="generate_bracket"),
    path("tournament/<str:admin_token>/bracket/", views.bracket_view, name="bracket_view"),

    # Group stage actions
    path("tournament/<str:admin_token>/game/<int:game_id>/vote/", views.vote_cup, name="vote_cup"),
    path("tournament/<str:admin_token>/game/<int:game_id>/results/", views.group_results, name="group_results"),

    # Bracket actions
    path("tournament/<str:admin_token>/bracket/<int:game_id>/results/", views.bracket_results, name="bracket_results"),
    path("tournament/<str:admin_token>/bracket/<int:game_id>/edit/", views.bracket_edit, name="bracket_edit"),
    path("tournament/<str:admin_token>/admin/rematch/", views.rematch_tournament, name="rematch"),
    path("tournament/<str:admin_token>/admin/blacklist/", views.manage_blacklist, name="blacklist"),

    # Statistics (visible to both admin and viewer; stats token = admin_token or viewer_token)
    path("tournament/<str:admin_token>/admin/stats/", views.tournament_stats, name="stats_admin"),
    path("tournament/<str:viewer_token>/stats/", views.tournament_stats_viewer, name="stats_viewer"),
]
