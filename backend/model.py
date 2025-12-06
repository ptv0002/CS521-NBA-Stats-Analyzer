import pandas as pd
import numpy as np

DATA_FILE = "backend/data/players.csv"

df = pd.read_csv(DATA_FILE)

def list_players():
    return sorted(df["FirstName"].unique().tolist())


def get_player_averages(players_file, boxscores_file):
    players_df = pd.read_csv(players_file)
    boxscores_df = pd.read_csv(boxscores_file)

    # Rename columns to match
    players_df = players_df.rename(columns={"Id": "PLAYER_ID"})
    boxscores_df = boxscores_df.rename(columns={"personId": "PLAYER_ID"})

    # Filter box scores
    filtered = boxscores_df[
        boxscores_df["PLAYER_ID"].isin(players_df["PLAYER_ID"])
    ]

    # Group + average
    averages = (
        filtered
        .groupby("PLAYER_ID")
        .mean(numeric_only=True)
        .reset_index()
    )

    # Merge info
    full = pd.merge(
        averages,
        players_df,
        on="PLAYER_ID",
        how="left"
    )

    full = full.replace([np.nan, np.inf, -np.inf], None)

    return full
