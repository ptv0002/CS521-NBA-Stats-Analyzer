import os
from flask import Flask, render_template, jsonify
import pandas as pd
from datetime import datetime, date
import numpy as np


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
PLAYER_STATS_FILE = os.path.join(DATA_DIR, "PlayerStatistics.csv")
TEAMS_FILE = os.path.join(DATA_DIR, "teams.csv")
TEAM_STATS_FILE = os.path.join(DATA_DIR, "TeamStatistics.csv")

df_players = pd.read_csv(PLAYERS_FILE)
df_teams = pd.read_csv(TEAMS_FILE)
df_teams = df_teams.rename(columns={"Id": "TeamId"})
df_player_stats = pd.read_csv(PLAYER_STATS_FILE)
df_team_stats = pd.read_csv(TEAM_STATS_FILE)

# --------- For teams and players file -----------
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
# Map old cities to current cities
TEAM_CITY_MAP = {
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

TEAM_NAME_MAP = {
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

# Boxscore columns for players (lowercase to match df_player_stats)
PLAYER_BOX_SCORE_COLS = [
    "points", "assists", "blocks", "steals",
    "fieldgoalsattempted", "fieldgoalsmade", "fieldgoalspercentage",
    "threepointersattempted", "threepointersmade", "threepointerspercentage",
    "freethrowsattempted", "freethrowsmade", "freethrowspercentage",
    "reboundsdefensive", "reboundsoffensive", "reboundstotal",
    "foulspersonal", "turnovers", "plusminuspoints",
]

STATS_TO_AVERAGE = [
    "assists", "blocks", "steals",
    "fieldGoalsAttempted", "fieldGoalsMade", "fieldGoalsPercentage",
    "threePointersAttempted", "threePointersMade", "threePointersPercentage",
    "freeThrowsAttempted", "freeThrowsMade", "freeThrowsPercentage",
    "reboundsDefensive", "reboundsOffensive", "reboundsTotal",
    "foulsPersonal", "turnovers", "plusMinusPoints",
    "teamScore", "opponentScore",
]

PERCENTAGE_COLS = [
    "fieldGoalsPercentage",
    "threePointersPercentage",
    "freeThrowsPercentage",
]
# Normalize column names to lower-case without spaces, similar to your old route
df_player_stats.columns = [c.strip().lower() for c in df_player_stats.columns]

# Build a consistent "player" full-name column
if "firstname" in df_player_stats.columns and "lastname" in df_player_stats.columns:
    df_player_stats["player"] = (
        df_player_stats["firstname"].astype(str).str.strip()
        + " "
        + df_player_stats["lastname"].astype(str).str.strip()
    )
else:
    # Fallback if the CSV already has a fullname column
    df_player_stats["player"] = df_player_stats.get("fullname", "")

df_team_stats["teamCity"] = df_team_stats["teamCity"].replace(TEAM_CITY_MAP)
df_team_stats["teamName"] = df_team_stats["teamName"].replace(TEAM_NAME_MAP)
df_team_stats["team"] = df_team_stats["teamCity"] + " " + df_team_stats["teamName"]

# Only keep modern NBA teams
df_team_stats = df_team_stats[df_team_stats["team"].isin(MODERN_TEAMS)]

def get_team_averages():
    # Only keep columns that actually exist
    cols = [c for c in STATS_TO_AVERAGE if c in df_team_stats.columns]

    # Compute averages per team
    averages = (
        df_team_stats
        .groupby("team")[cols]
        .mean(numeric_only=True)
        .round(3)
        .reset_index()
    )

    # Fix percentage columns (0–100 scale, 1 decimal place)
    averages = _fix_percentage_columns(averages, PERCENTAGE_COLS)

    # Reorder columns
    column_order = ["team"] + cols
    return averages[column_order]


def get_player_averages():
    """
    Returns a DataFrame with per-player per-game averages
    from the preloaded df_player_stats (PlayerStatistics.csv).
    """
    # Only keep columns that actually exist in the CSV
    cols = [c for c in PLAYER_BOX_SCORE_COLS if c in df_player_stats.columns]

    averages = (
        df_player_stats
        .groupby("player")[cols]
        .mean(numeric_only=True)
        .round(3)   # keep a few decimals, then adjust percentages
        .reset_index()
    )

    # Fix percentages
    averages = _fix_percentage_columns(averages, PERCENTAGE_COLS)

    # Nice column name for frontend
    averages = averages.rename(columns={"player": "Player"})

    return averages


def get_team_timeseries(team_name: str) -> pd.DataFrame:
    if df_team_stats.empty:
        return pd.DataFrame()

    # Filter to just this team (df_team_stats is already mapped + filtered to MODERN_TEAMS)
    df = df_team_stats[df_team_stats["team"] == team_name].copy()
    if df.empty:
        return pd.DataFrame()

    # Derive season
    if "season" in df.columns:
        season_col = "season"
    elif "gameDateTimeEst" in df.columns:
        # Parse the datetime and take the calendar year as the season ID
        df["season"] = pd.to_datetime(df["gameDateTimeEst"], errors="coerce").dt.year
        season_col = "season"
    else:
        # Fallback: treat everything as one season
        df["season"] = 0
        season_col = "season"

    # Only average columns that actually exist
    cols = [c for c in STATS_TO_AVERAGE if c in df.columns]

    timeseries = (
        df
        .groupby(season_col)[cols]
        .mean(numeric_only=True)
        .round(3)
        .reset_index()
        .sort_values(season_col)
    )

    # Fix percentage columns (0–100)
    timeseries = _fix_percentage_columns(timeseries, PERCENTAGE_COLS)

    # Standardize column name and add team name
    timeseries = timeseries.rename(columns={season_col: "season"})
    timeseries["team"] = team_name

    # Final column order: season, team, then all stats we kept
    return timeseries[["season", "team"] + cols]



def _fix_percentage_columns(df, percentage_cols):
    """
    Convert 0–1 percentages to 0–100 and round to 1 decimal place.
    """
    for col in percentage_cols:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: x * 100 if pd.notnull(x) and x <= 1 else x)
            df[col] = df[col].round(1)
    return df
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

@app.route("/charts")
def charts():
    return render_template("charts.html")
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

# @app.route("/api/player-names")
# def api_player_names():
#     names = sorted(df_players["FullName"].dropna().unique().tolist())
#     return jsonify(names)

@app.route("/api/teams")
def api_teams():
    display_df = df_teams.rename(columns={
        "YearFounded": "Year Founded",
    })
    records = display_df.to_dict(orient="records")
    return jsonify(records)

@app.route("/api/team_averages")
def team_averages():
    display_df = get_team_averages()

    # Merge to get Abbreviation + Division from df_teams
    merged = display_df.merge(
        df_teams[["TeamName", "Abbreviation", "Division"]],
        left_on="team",
        right_on="TeamName",
        how="left"
    )

    merged = merged.rename(columns={
        "Abbreviation": "abbreviation",
        "Division": "division"
    }).drop(columns=["TeamName"])

    records = merged.to_dict(orient="records")
    return jsonify(records)

@app.route("/api/player_averages")
def api_player_averages_all():
    display_df = get_player_averages()
    records = display_df.to_dict(orient="records")
    return jsonify(records)

@app.route("/api/team_timeseries/<team_name>")
def api_team_timeseries(team_name):
    from urllib.parse import unquote
    team_name_clean = unquote(team_name)
    df_ts = get_team_timeseries(team_name_clean)
    if df_ts.empty:
        return jsonify([])

    df_ts = df_ts.replace({np.nan: None})
    return jsonify(df_ts.to_dict(orient="records"))

# ------------------------------------------------------------------
# Main entry point
# ------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)
