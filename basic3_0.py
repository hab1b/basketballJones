import streamlit as st
from nba_api.stats.endpoints import playergamelog
from nba_api.stats.static import players, teams
import pandas as pd
import time

st.set_page_config(page_title="NBA Player Matchup Stats", layout="centered")
st.title("Little Bucket Book")

# === INPUTS ===
player_name = st.text_input("Player Name", value="Jayson Tatum")
opponent_team = st.text_input("Opponent Team", value="Miami Heat")
num_games = st.slider("Number of Games", 1, 20, 10)

stat_targets = ["PTS", "REB", "AST", "FG3M", "FG3A"]
seasons = ["2024-25", "2023-24", "2022-23", "2021-22", "2020-21", "2019-20"]

def get_team_abbreviation(name):
    return next(team['abbreviation'] for team in teams.get_teams() if team['full_name'] == name)

def get_player_id(name):
    return players.find_players_by_full_name(name)[0]['id']

# === MAIN LOGIC ===
if st.button("Run Analysis"):
    try:
        opp_abbr = get_team_abbreviation(opponent_team)
        player_id = get_player_id(player_name)

        all_games = pd.DataFrame()
        for season in seasons:
            log = playergamelog.PlayerGameLog(player_id=player_id, season=season).get_data_frames()[0]
            vs_team = log[log['MATCHUP'].str.contains(opp_abbr)]
            all_games = pd.concat([all_games, vs_team])
            if len(all_games) >= num_games:
                break
            time.sleep(0.6)

        all_games = all_games.head(num_games)
        st.subheader(f"📊 {player_name}'s Last {len(all_games)} Games vs {opponent_team}")
        st.dataframe(all_games[["SEASON_ID", "GAME_DATE", "MATCHUP"] + stat_targets])

        # Also show overall last 10 games
        log_recent = playergamelog.PlayerGameLog(player_id=player_id, season=seasons[0]).get_data_frames()[0]
        overall_stats = log_recent.head(num_games)[["GAME_DATE", "MATCHUP"] + stat_targets]

        st.subheader(f"📈 Last {num_games} Overall Games")
        st.dataframe(overall_stats)

    except Exception as e:
        st.error(f"❌ Something went wrong: {e}")
