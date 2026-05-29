import sqlite3
import time
import os
from nba_api.stats.endpoints import teamgamelog
from nba_api.stats.static import teams as nba_teams_static

DB_PATH = os.path.join(os.path.dirname(__file__), 'nba.db')
SEASONS = ['2020-21', '2021-22', '2022-23', '2023-24', '2024-25', '2025-26']
SEASON_TYPES = ['Regular Season', 'Playoffs']

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_connection()
    schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
    with open(schema_path, 'r') as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()
    print('Banco inicializado.', flush=True)

def get_all_teams():
    return nba_teams_static.get_teams()

def calc_ts_pct(pts, fga, fta):
    denominator = 2 * (fga + 0.44 * fta)
    if denominator == 0:
        return 0.0
    return pts / denominator

def calc_pace(fga, oreb, tov, fta):
    return fga - oreb + tov + (0.44 * fta)

def collect_team_season(team_id, season, season_type):
    try:
        gamelog = teamgamelog.TeamGameLog(
            team_id=team_id,
            season=season,
            season_type_all_star=season_type
        )
        df = gamelog.get_data_frames()[0]
        time.sleep(0.6)
        return df
    except Exception as e:
        print(f'Erro ao coletar {team_id} {season} {season_type}: {e}', flush=True)
        return None

def parse_matchup(matchup):
    return 1 if 'vs.' in matchup else 0

def get_opponent_tricode(matchup):
    parts = matchup.replace('vs.', '@').split('@')
    return parts[-1].strip()

def get_team_tricode(matchup):
    return matchup.split(' ')[0].strip()

def save_team_games(df, team_id, season, season_type, conn):
    cursor = conn.cursor()
    is_playoff = 1 if season_type == 'Playoffs' else 0

    for _, row in df.iterrows():
        game_id = row['Game_ID']
        is_home = parse_matchup(row['MATCHUP'])
        team_tricode = get_team_tricode(row['MATCHUP'])
        ts_pct = calc_ts_pct(row['PTS'], row['FGA'], row['FTA'])
        pace = calc_pace(row['FGA'], row['OREB'], row['TOV'], row['FTA'])

        cursor.execute('''
            INSERT OR IGNORE INTO team_game_stats
            (game_id, team_id, is_home, fgm, fga, fg_pct, fg3m, fg3a, fg3_pct,
             ftm, fta, ft_pct, oreb, dreb, reb, ast, stl, blk, tov, pts, ts_pct, pace)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            game_id, team_id, is_home,
            row['FGM'], row['FGA'], row['FG_PCT'],
            row['FG3M'], row['FG3A'], row['FG3_PCT'],
            row['FTM'], row['FTA'], row['FT_PCT'],
            row['OREB'], row['DREB'], row['REB'],
            row['AST'], row['STL'], row['BLK'],
            row['TOV'], row['PTS'], ts_pct, pace
        ))

        if is_home:
            home_win = 1 if row['WL'] == 'W' else 0
            cursor.execute('''
                INSERT OR IGNORE INTO games
                (game_id, game_date, season, season_type,
                 home_team_id, home_team_tricode,
                 home_score, home_win, is_playoff)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                game_id, row['GAME_DATE'], season, season_type,
                team_id, team_tricode,
                row['PTS'], home_win, is_playoff
            ))
        else:
            cursor.execute('''
                UPDATE games SET
                    away_team_id = ?,
                    away_team_tricode = ?,
                    away_score = ?,
                    total_points = home_score + ?
                WHERE game_id = ?
            ''', (
                team_id, team_tricode,
                row['PTS'], row['PTS'], game_id
            ))

    conn.commit()

def collect_all():
    init_db()
    all_teams = get_all_teams()
    total = len(all_teams) * len(SEASONS) * len(SEASON_TYPES)
    count = 0

    conn = get_connection()

    for season in SEASONS:
        for season_type in SEASON_TYPES:
            for team in all_teams:
                count += 1
                team_id = team['id']
                print(f'[{count}/{total}] {team["abbreviation"]} — {season} {season_type}', flush=True)

                df = collect_team_season(team_id, season, season_type)
                if df is not None and not df.empty:
                    save_team_games(df, team_id, season, season_type, conn)

    conn.close()
    print('Coleta concluída!', flush=True)

if __name__ == '__main__':
    collect_all()