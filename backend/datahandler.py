import pandas as pd

# Load player list and box scores
boxscores_df = pd.read_csv("data/PlayerStatistics.csv")
players_df = pd.read_csv("data/players.csv")


# Rename columns to match
players_df = players_df.rename(columns={"Id": "PLAYER_ID"})
boxscores_df = boxscores_df.rename(columns={"personId": "PLAYER_ID"})

# Filter box scores to only include players in your list
filtered_boxscores = boxscores_df[boxscores_df["PLAYER_ID"].isin(players_df["PLAYER_ID"])]

# Group by PLAYER_ID and take mean of numeric stats
player_averages = filtered_boxscores.groupby("PLAYER_ID").mean(numeric_only=True).reset_index()

# Merge with player names or team info from players_df
player_averages_full = pd.merge(player_averages, players_df, on="PLAYER_ID", how="left")

# Check the result
print(player_averages_full.head())
