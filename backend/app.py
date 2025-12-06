import os
from flask import Flask, render_template, jsonify
import pandas as pd
from datetime import datetime, date


# ------------------------------------------------------------------
# Paths
# ------------------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))   # .../backend
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))

TEMPLATE_DIR = os.path.join(PROJECT_ROOT, "frontend", "templates")
STATIC_DIR   = os.path.join(PROJECT_ROOT, "frontend", "static")

# Optional: debug prints so you can see paths
print("TEMPLATE_DIR:", TEMPLATE_DIR)
print("STATIC_DIR:", STATIC_DIR)

# ------------------------------------------------------------------
# Flask app setup (point to the correct folders)
# ------------------------------------------------------------------

app = Flask(
    __name__,
    template_folder=TEMPLATE_DIR,
    static_folder=STATIC_DIR,
    static_url_path="/static",  # URL prefix for static files
)

# ------------------------------------------------------------------
# Load CSV data once at startup
# ------------------------------------------------------------------

DATA_DIR = os.path.join(BASE_DIR, "data")
PLAYERS_FILE = os.path.join(DATA_DIR, "players.csv")
TEAMS_FILE = os.path.join(DATA_DIR, "teams.csv")
TEAM_STATS_FILE = os.path.join(DATA_DIR, "TeamStatistics.csv")

df_players = pd.read_csv(PLAYERS_FILE)
df_teams = pd.read_csv(TEAMS_FILE)
df_teams = df_teams.rename(columns={"Id": "TeamId"})


# Create FullName column
if "FirstName" in df_players.columns and "LastName" in df_players.columns:
    df_players["FullName"] = df_players["FirstName"].astype(str) + " " + df_players["LastName"].astype(str)
else:
    df_players["FullName"] = ""

# Compute Age column
today = date.today()
if "DateOfBirth" in df_players.columns:
    # Convert column to datetime safely
    df_players["DateOfBirth"] = pd.to_datetime(df_players["DateOfBirth"], errors="coerce")

    # Calculate age vectorized
    df_players["Age"] = df_players["DateOfBirth"].apply(
        lambda dob: today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        if pd.notnull(dob) else None
    )
else:
    df_players["Age"] = None

# Create Team Full Name Column
df_teams = df_teams.rename(columns={"Id": "TeamId"})
if "City" in df_teams.columns and "Nickname" in df_teams.columns:
    df_teams["TeamName"] = df_teams["City"].astype(str) + " " + df_teams["Nickname"].astype(str)
else:
    df_players["TeamName"] = ""
if "TeamId" in df_players.columns and "TeamId" in df_teams.columns:
    df_players = df_players.merge(
        df_teams[["TeamId", "TeamName"]],
        on="TeamId",
        how="left"
    )
else:
    df_players["TeamName"] = ""

# ------------------------------------------------------------------
# Process Team, Player, Game Statistics
# ------------------------------------------------------------------
# List of modern NBA teams
MODERN_TEAMS = [
    "Atlanta Hawks", "Boston Celtics", "Brooklyn Nets", "Charlotte Hornets",
    "Chicago Bulls", "Cleveland Cavaliers", "Dallas Mavericks", "Denver Nuggets",
    "Detroit Pistons", "Golden State Warriors", "Houston Rockets", "Indiana Pacers",
    "Los Angeles Clippers", "Los Angeles Lakers", "Memphis Grizzlies", "Miami Heat",
    "Milwaukee Bucks", "Minnesota Timberwolves", "New Orleans Pelicans", "New York Knicks",
    "Oklahoma City Thunder", "Orlando Magic", "Philadelphia 76ers", "Phoenix Suns",
    "Portland Trail Blazers", "Sacramento Kings", "San Antonio Spurs", "Toronto Raptors",
    "Utah Jazz", "Washington Wizards"
]

def get_team_averages():
    # Load team games CSV
    df_team_stats = pd.read_csv(TEAM_STATS_FILE)

    stats_to_average = [
        "assists", "blocks", "steals",
        "fieldGoalsAttempted", "fieldGoalsMade", "fieldGoalsPercentage",
        "threePointersAttempted", "threePointersMade", "threePointersPercentage",
        "freeThrowsAttempted", "freeThrowsMade", "freeThrowsPercentage",
        "reboundsDefensive", "reboundsOffensive", "reboundsTotal",
        "foulsPersonal", "turnovers", "plusMinusPoints",
        "teamScore", "opponentScore"
    ]

    # Map old cities to current cities
    team_city_map = {
        "St. Louis": "Atlanta",
        "San Diego": "Los Angeles",
        "Cincinnati": "Sacramento",
        "Tri-Cities": "Atlanta",
        "New Jersey": "Brooklyn",
        "Minneapolis": "Los Angeles",
        "Baltimore": "Washington",
        "Kansas City": "Sacramento",
        "Vancouver": "Memphis",
        "Seattle": "Oklahoma City",
    }

    team_name_map = {
        "Royals": "Kings",
        "Bullets": "Wizards",
        "Hawks": "Hawks",
        "Clippers": "Clippers",
        "Lakers": "Lakers",
        "Nets": "Nets",
        "Warriors": "Warriors",
        "Grizzlies": "Grizzlies",
        "SuperSonics": "Thunder",
    }

    df_team_stats["teamCity"] = df_team_stats["teamCity"].replace(team_city_map)
    df_team_stats["teamName"] = df_team_stats["teamName"].replace(team_name_map)
    df_team_stats["team"] = df_team_stats["teamCity"] + " " + df_team_stats["teamName"]

    # Only keep modern NBA teams
    df_team_stats = df_team_stats[df_team_stats["team"].isin(MODERN_TEAMS)]

    # Compute averages per team
    averages = (
        df_team_stats
        .groupby("team")[stats_to_average]
        .mean(numeric_only=True)
        .round(3)  # keep more decimals for percentages
        .reset_index()
    )

    # Correct percentage columns (0-100 scale)
    percentage_cols = [
        "fieldGoalsPercentage",
        "threePointersPercentage",
        "freeThrowsPercentage"
    ]
    for col in percentage_cols:
        if col in averages.columns:
            averages[col] = averages[col].apply(lambda x: x * 100 if x <= 1 else x)
            averages[col] = averages[col].round(1)

    # Reorder columns
    column_order = ["team"] + stats_to_average
    return averages[column_order]


def get_player_averages():
    """
    Returns a DataFrame with per-player averages from the TeamStatistics CSV.
    """
    df_stats = pd.read_csv(TEAM_STATS_FILE)

    # Combine player full name in stats
    if "firstName" in df_stats.columns and "lastName" in df_stats.columns:
        df_stats["Player"] = df_stats["firstName"].astype(str) + " " + df_stats["lastName"].astype(str)
    else:
        df_stats["Player"] = df_stats.get("FullName", "")

    # Stats to average
    stats_to_average = [
        "assists", "blocks", "steals",
        "fieldGoalsAttempted", "fieldGoalsMade", "fieldGoalsPercentage",
        "threePointersAttempted", "threePointersMade", "threePointersPercentage",
        "freeThrowsAttempted", "freeThrowsMade", "freeThrowsPercentage",
        "reboundsDefensive", "reboundsOffensive", "reboundsTotal",
        "foulsPersonal", "turnovers", "plusMinusPoints",
        "teamScore", "opponentScore"
    ]

    # Group by player
    averages = (
        df_stats
        .groupby("Player")[stats_to_average]
        .mean(numeric_only=True)
        .round(3)
        .reset_index()
    )

    # Correct percentages (0–100 scale)
    percentage_cols = ["fieldGoalsPercentage", "threePointersPercentage", "freeThrowsPercentage"]
    for col in percentage_cols:
        if col in averages.columns:
            averages[col] = averages[col].apply(lambda x: x * 100 if x <= 1 else x)
            averages[col] = averages[col].round(1)

    return averages


# ------------------------------------------------------------------
# Routes that render HTML pages
# ------------------------------------------------------------------

@app.route("/")
def home():
    # This will look for frontend/templates/home.html
    return render_template("home.html", title="Home Page")


@app.route("/players")
def players_page():
    # This will look for frontend/templates/players.html
    return render_template("players.html", title="Player Stats")

@app.route("/teams")
def teams_page():
    # This will look for frontend/templates/teams.html
    return render_template("teams.html", title="Team Stats")
# ------------------------------------------------------------------
# API routes that return JSON
# ------------------------------------------------------------------

@app.route("/api/players")
def api_players():
    display_df = df_players.rename(columns={
        "FirstName": "First Name",
        "LastName": "Last Name",
        "DateOfBirth": "Date of Birth",
        "FullName": "Player",
        "TeamName": "Team",
        "School": "Last Attended",
    })
    display_df["FullName"] = df_players["FirstName"].astype(str) + " " + df_players["LastName"].astype(str)
    records = display_df.to_dict(orient="records")
    return jsonify(records)

@app.route("/api/player-names")
def api_player_names():
    names = sorted(df_players["FullName"].dropna().unique().tolist())
    return jsonify(names)

@app.route("/api/teams")
def api_teams():
    display_df = df_teams.rename(columns={
        "YearFounded": "Year Founded",
    })
    records = display_df.to_dict(orient="records")
    return jsonify(records)

@app.route("/charts")
def charts():
    return render_template("charts.html")

@app.route("/api/team_averages")
def team_averages():
    display_df = get_team_averages()
    records = display_df.to_dict(orient="records")
    return jsonify(records)

@app.route("/api/player-averages/<player_name>")
def api_player_averages(player_name):
    import pandas as pd
    from urllib.parse import unquote

    DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
    df_stats = pd.read_csv(os.path.join(DATA_DIR, "PlayerStatistics.csv"))

    # Normalize column names
    df_stats.columns = [c.strip().lower() for c in df_stats.columns]

    # Build full name safely
    df_stats["fullname"] = df_stats["firstname"].astype(str).str.strip() + " " + df_stats["lastname"].astype(str).str.strip()

    # Normalize the incoming player name
    player_name_clean = unquote(player_name).strip().lower()

    # Lookup
    player_stats = df_stats[df_stats["fullname"].str.lower() == player_name_clean]

    if player_stats.empty:
        return jsonify({"error": "Player not found"}), 404

    # Boxscore stats columns
    boxscore_cols = [
        "points", "assists", "blocks", "steals",
        "fieldgoalsattempted", "fieldgoalsmade", "fieldgoalspercentage",
        "threepointersattempted", "threepointersmade", "threepointerspercentage",
        "freethrowsattempted", "freethrowsmade", "freethrowspercentage",
        "reboundsdefensive", "reboundsoffensive", "reboundstotal",
        "foulspersonal", "turnovers", "plusminuspoints"
    ]

    # Make sure only existing columns are used
    boxscore_cols = [c for c in boxscore_cols if c in player_stats.columns]

    per_game = player_stats[boxscore_cols].mean(numeric_only=True).round(1)
    per_game["FullName"] = player_name

    return jsonify(per_game.to_dict())


# ------------------------------------------------------------------
# Main entry point
# ------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)
