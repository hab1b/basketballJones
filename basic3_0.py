import streamlit as st
from nba_api.stats.endpoints import playergamelog, commonteamroster
from nba_api.stats.static import players, teams
import pandas as pd
import time

st.set_page_config(page_title="NBA Player Matchup Stats", layout="centered")
st.title("Little Bucket Book")

# === SETUP ===
team_list = sorted(teams.get_teams(), key=lambda x: x['full_name'])
team_names = [team['full_name'] for team in team_list]
stat_targets = ["PTS", "REB", "AST", "FG3M", "FG3A"]
seasons = ["2024-25", "2023-24", "2022-23", "2021-22", "2020-21", "2019-20"]

# === HELPERS ===
def get_team_by_name(name):
    return next(team for team in team_list if team['full_name'] == name)

def get_team_abbreviation(name):
    return get_team_by_name(name)['abbreviation']

def get_team_id(name):
    return get_team_by_name(name)['id']

def get_player_id(name):
    return players.find_players_by_full_name(name)[0]['id']

def get_roster(team_id, season):
    df = commonteamroster.CommonTeamRoster(team_id=team_id, season=season).get_data_frames()[0]
    return df['PLAYER'].tolist()

def get_full_season_log(player_id, season):
    """Concatenate regular season + playoffs"""
    reg = playergamelog.PlayerGameLog(player_id=player_id, season=season, season_type_all_star="Regular Season").get_data_frames()[0]
    playoffs = playergamelog.PlayerGameLog(player_id=player_id, season=season, season_type_all_star="Playoffs").get_data_frames()[0]
    return pd.concat([reg, playoffs], ignore_index=True)

# === INPUTS ===
selected_team = st.selectbox("Select Team", team_names, index=team_names.index("Boston Celtics"))
team_id = get_team_id(selected_team)
roster_players = get_roster(team_id, seasons[0])

player_name = st.selectbox("Select Player", sorted(roster_players), index=roster_players.index("Jayson Tatum") if "Jayson Tatum" in roster_players else 0)
opponent_team = st.selectbox("Select Opponent Team", [t for t in team_names if t != selected_team], index=team_names.index("Miami Heat"))
num_games = st.slider("Number of Games", 1, 20, 10)

# === MAIN LOGIC ===
if st.button("Run Analysis"):
    try:
        opp_abbr = get_team_abbreviation(opponent_team)
        player_id = get_player_id(player_name)

        all_games = pd.DataFrame()
        for season in seasons:
            full_log = get_full_season_log(player_id, season)
            vs_team = full_log[full_log['MATCHUP'].str.contains(opp_abbr)]
            all_games = pd.concat([all_games, vs_team])
            if len(all_games) >= num_games:
                break
            time.sleep(0.6)

        # Fix: parse dates properly before sorting
        all_games["GAME_DATE"] = pd.to_datetime(all_games["GAME_DATE"])
        all_games = all_games.sort_values("GAME_DATE", ascending=False).head(num_games)
        all_games["GAME_DATE"] = all_games["GAME_DATE"].dt.strftime("%b %d, %Y")

        st.subheader(f"📊 {player_name}'s Last {len(all_games)} Games vs {opponent_team}")
        st.dataframe(all_games[["SEASON_ID", "GAME_DATE", "MATCHUP"] + stat_targets])

        # Also show recent games overall (with playoffs)
        full_recent = get_full_season_log(player_id, seasons[0])
        full_recent["GAME_DATE"] = pd.to_datetime(full_recent["GAME_DATE"])
        full_recent = full_recent.sort_values("GAME_DATE", ascending=False)
        overall_stats = full_recent.head(num_games)[["GAME_DATE", "MATCHUP"] + stat_targets]
        overall_stats["GAME_DATE"] = overall_stats["GAME_DATE"].dt.strftime("%b %d, %Y")

        st.subheader(f"📈 Last {num_games} Overall Games")
        st.dataframe(overall_stats)

    except Exception as e:
        st.error(f"❌ Something went wrong: {e}")