"""Mario Kart 8 Deluxe cup list and other constants."""

# All cups available in Mario Kart 8 Deluxe
CUPS = [
    # Base game
    "Mushroom",
    "Flower",
    "Star",
    "Special",
    "Shell",
    "Banana",
    "Leaf",
    "Lightning",
    # Booster Course Pass DLC
    "Golden Dash",
    "Lucky Cat",
    "Turnip",
    "Propeller",
    "Rock",
    "Moon",
    "Fruit",
    "Boomerang",
    # Additional DLC
    "Feather",
    "Cherry",
    "Acorn",
    "Spiny",
    "Egg",
    "Triforce",
    "Crossing",
    "Bell",
]

CUPS_CHOICES = [(cup, cup) for cup in CUPS]

# Tournament stage constants
STAGE_SETUP = "setup"
STAGE_GROUP = "group"
STAGE_BRACKET = "bracket"
STAGE_COMPLETE = "complete"

STAGE_CHOICES = [
    (STAGE_SETUP, "Setup"),
    (STAGE_GROUP, "Group Stage"),
    (STAGE_BRACKET, "Bracket"),
    (STAGE_COMPLETE, "Complete"),
]

# Game status constants
GAME_STATUS_PENDING = "pending"
GAME_STATUS_VOTING = "voting"
GAME_STATUS_IN_PROGRESS = "in_progress"
GAME_STATUS_COMPLETE = "complete"

GAME_STATUS_CHOICES = [
    (GAME_STATUS_PENDING, "Pending"),
    (GAME_STATUS_VOTING, "Voting"),
    (GAME_STATUS_IN_PROGRESS, "In Progress"),
    (GAME_STATUS_COMPLETE, "Complete"),
]

BRACKET_GAME_STATUS_CHOICES = [
    (GAME_STATUS_PENDING, "Pending"),
    (GAME_STATUS_COMPLETE, "Complete"),
]

MAX_PLAYERS_PER_GAME = 4
