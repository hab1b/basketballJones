import streamlit as st
from nba_api.stats.endpoints import playergamelog
from nba_api.stats.static import players, teams
import pandas as pd
import time

st.set_page_config(page_title="NBA Player Matchup Stats", layout="centered")
st.title("Little Bucket Book")

# === INPUTS ===
team_names = [team["full_name"] for team in teams.get_teams()]
selected_team = st.selectbox("Select Team", sorted(team_names))

# Filter players from selected team
team_id = next(team["id"] for team in teams.get_teams() if team["full_name"] == selected_team)
player_options = players.find_players_by_team_id(team_id)
player_name = st.selectbox("Select Player", [p["full_name"] for p in player_options])

opponent_team = st.selectbox("Opponent Team", sorted(team_names))
num_games = st.slider("Number of Matchup Games", 1, 20, 10)

# Predefined stat targets
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
            # Include both Regular Season and Playoffs
            log_regular = playergamelog.PlayerGameLog(player_id=player_id, season=season, season_type_all_star="Regular Season").get_data_frames()[0]
            log_playoffs = playergamelog.PlayerGameLog(player_id=player_id, season=season, season_type_all_star="Playoffs").get_data_frames()[0]

            full_log = pd.concat([log_regular, log_playoffs])
            vs_team = full_log[full_log['MATCHUP'].str.contains(opp_abbr)]
            all_games = pd.concat([all_games, vs_team])
            if len(all_games) >= num_games:
                break
            time.sleep(0.6)

        all_games = all_games.sort_values("GAME_DATE", ascending=False).head(num_games)
        st.subheader(f"📊 {player_name}'s Last {len(all_games)} Games vs {opponent_team}")
        st.dataframe(all_games[["SEASON_ID", "GAME_DATE", "MATCHUP"] + stat_targets])

        # Also show overall last 10 games
        log_regular = playergamelog.PlayerGameLog(player_id=player_id, season=seasons[0], season_type_all_star="Regular Season").get_data_frames()[0]
        log_playoffs = playergamelog.PlayerGameLog(player_id=player_id, season=seasons[0], season_type_all_star="Playoffs").get_data_frames()[0]
        full_recent = pd.concat([log_regular, log_playoffs]).sort_values("GAME_DATE", ascending=False)
        recent_games = full_recent.head(num_games)

        st.subheader(f"📈 Last {num_games} Overall Games")
        st.dataframe(recent_games[["GAME_DATE", "MATCHUP"] + stat_targets])

    except Exception as e:
        st.error(f"❌ Something went wrong: {e}")
