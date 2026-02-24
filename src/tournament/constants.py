"""Mario Kart 8 Deluxe cup list and other constants."""

# All cups and their tracks in Mario Kart 8 Deluxe (96 tracks total)
CUP_TRACKS = {
    # Base game — nitro cups
    "Mushroom": [
        "Mario Kart Stadium",
        "Water Park",
        "Sweet Sweet Canyon",
        "Thwomp Ruins",
    ],
    "Flower": [
        "Mario Circuit",
        "Toad Harbor",
        "Twisted Mansion",
        "Shy Guy Falls",
    ],
    "Star": [
        "Sunshine Airport",
        "Dolphin Shoals",
        "Electrodrome",
        "Mount Wario",
    ],
    "Special": [
        "Cloudtop Cruise",
        "Bone-Dry Dunes",
        "Bowser's Castle",
        "Rainbow Road",
    ],
    # Base game — retro cups
    "Shell": [
        "Moo Moo Meadows",
        "Mario Circuit (GBA)",
        "Cheep Cheep Beach",
        "Toad's Turnpike",
    ],
    "Banana": [
        "Dry Dry Desert",
        "Donut Plains 3",
        "Royal Raceway",
        "DK Jungle",
    ],
    "Leaf": [
        "Wario Stadium",
        "Sherbet Land",
        "Music Park",
        "Yoshi Valley",
    ],
    "Lightning": [
        "Koopa Troopa Beach",
        "Mario Circuit (GCN)",
        "Maple Treeway",
        "Grumble Volcano",
    ],
    # Booster Course Pass — Wave 1
    "Golden Dash": [
        "Paris Promenade",
        "Toad Circuit",
        "Choco Mountain",
        "Coconut Mall",
    ],
    "Lucky Cat": [
        "Tokyo Blur",
        "Shroom Ridge",
        "Sky Garden",
        "Ninja Hideaway",
    ],
    # Booster Course Pass — Wave 2
    "Turnip": [
        "New York Minute",
        "Mario Circuit 3",
        "Kalimari Desert",
        "Waluigi Pinball",
    ],
    "Propeller": [
        "Sydney Sprint",
        "Snow Land",
        "Mushroom Gorge",
        "Sky-High Sundae",
    ],
    # Booster Course Pass — Wave 3
    "Rock": [
        "London Loop",
        "Boo Lake",
        "Rock Rock Mountain",
        "Maple Treeway (Wii)",
    ],
    "Moon": [
        "Berlin Byways",
        "Singapore Speedway",
        "Old Koopa Raceway",
        "Airship Fortress",
    ],
    # Booster Course Pass — Wave 4
    "Fruit": [
        "Amsterdam Drift",
        "Riverside Park",
        "DK Summit",
        "Yoshi's Island",
    ],
    "Boomerang": [
        "Bangkok Rush",
        "Mario Circuit (DS)",
        "Waluigi Stadium",
        "Koopa Cape",
    ],
    # Booster Course Pass — Wave 5
    "Feather": [
        "Tour Los Angeles Laps",
        "Sunset Wilds",
        "Koopa Troopa Beach (3DS)",
        "Rome Avanti",
    ],
    "Cherry": [
        "Madrid Drive",
        "Rosalina's Ice World",
        "Rainbow Road (SNES)",
        "Rainbow Road (3DS)",
    ],
    # Booster Course Pass — Wave 6
    "Acorn": [
        "Athens Dash",
        "Daisy Circuit",
        "Peach Gardens",
        "Merry Mountain",
    ],
    "Spiny": [
        "Tour Melbourne Glide",
        "Bowser Castle 3",
        "Rainbow Road (N64)",
        "Rainbow Road (Wii)",
    ],
    # Battle courses repurposed as cups (these are approximate)
    "Egg": [
        "Wario's Gold Mine",
        "Rainbow Road (GBA)",
        "Ice Ice Outpost",
        "Hyrule Circuit",
    ],
    "Triforce": [
        "Baby Park",
        "Cheese Land",
        "Wild Woods",
        "Animal Crossing",
    ],
    "Crossing": [
        "Super Bell Subway",
        "Big Blue",
        "Dragon Driftway",
        "Mute City",
    ],
    "Bell": [
        "Cloudtop Cruise (Alt)",
        "Bone-Dry Dunes (Alt)",
        "Neo Bowser City",
        "Ribbon Road",
    ],
}

# Flat list of all cups (for choices, iteration, etc.)
CUPS = list(CUP_TRACKS.keys())

CUPS_CHOICES = [(cup, cup) for cup in CUPS]

# All individual tracks as a flat list (for random track selection)
ALL_TRACKS = [
    {"cup": cup, "track": track}
    for cup, tracks in CUP_TRACKS.items()
    for track in tracks
]

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
