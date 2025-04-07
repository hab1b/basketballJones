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
        full_game_log = pd.DataFrame()

        for season in seasons:
            log = playergamelog.PlayerGameLog(player_id=player_id, season=season).get_data_frames()[0]
            if full_game_log.empty:
                full_game_log = log.copy()
            else:
                full_game_log = pd.concat([full_game_log, log])

            vs_team = log[log['MATCHUP'].str.contains(opp_abbr)]
            all_games = pd.concat([all_games, vs_team])
            if len(all_games) >= num_games:
                break
            time.sleep(0.6)

        all_games = all_games.head(num_games)
        st.subheader(f"📊 {player_name}'s Last {len(all_games)} Games vs {opponent_team}")
        st.dataframe(all_games[["SEASON_ID", "GAME_DATE", "MATCHUP"] + stat_targets])

        # Also show overall last 10 games
        log_recent = full_game_log.copy()
        overall_stats = log_recent.head(num_games)[["GAME_DATE", "MATCHUP"] + stat_targets]

        st.subheader(f"📈 Last {num_games} Overall Games")
        st.dataframe(overall_stats)

        # === BONUS: SUPER BOOST FEATURE ===
        with st.expander("💥 Bonus: Performance vs Usual Form"):
            comparisons = []
            full_game_log = full_game_log.reset_index(drop=True)

            for _, matchup_row in all_games.iterrows():
                game_id = matchup_row['GAME_ID']
                idx = full_game_log[full_game_log['GAME_ID'] == game_id].index
                if len(idx) == 0:
                    continue

                idx = idx[0]
                before = full_game_log.iloc[idx+1:idx+4]  # 3 games before
                after = full_game_log.iloc[max(0, idx-3):idx]  # 3 games after

                entry = {
                    "GAME_DATE": matchup_row["GAME_DATE"],
                    "MATCHUP": matchup_row["MATCHUP"]
                }

                for stat in stat_targets:
                    match_val = matchup_row[stat]
                    before_avg = before[stat].astype(float).mean() if not before.empty else None
                    after_avg = after[stat].astype(float).mean() if not after.empty else None
                    deviation = match_val - ((before_avg + after_avg) / 2) if before_avg and after_avg else None
                    entry[f"{stat}_BEFORE3"] = round(before_avg, 1) if before_avg else None
                    entry[f"{stat}_AFTER3"] = round(after_avg, 1) if after_avg else None
                    entry[f"{stat}_DEV"] = round(deviation, 1) if deviation else None

                comparisons.append(entry)

            comparison_df = pd.DataFrame(comparisons)
            st.dataframe(comparison_df)

    except Exception as e:
        st.error(f"❌ Something went wrong: {e}")
