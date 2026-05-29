import sqlite3
import time
import os
from nba_api.stats.endpoints import leaguegamefinder
from nba_api.stats.static import teams as nba_teams_static

DATA_PATH = os.environ.get('DATA_PATH', os.path.dirname(__file__))
DB_PATH = os.path.join(DATA_PATH, 'nba.db')
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

def calc_ts_pct(pts, fga, fta):
    denominator = 2 * (fga + 0.44 * fta)
    if denominator == 0:
        return 0.0
    return pts / denominator

def calc_pace(fga, oreb, tov, fta):
    return fga - oreb + tov + (0.44 * fta)

def collect_season(season, season_type):
    try:
        finder = leaguegamefinder.LeagueGameFinder(
            season_nullable=season,
            season_type_nullable=season_type,
            league_id_nullable='00'
        )
        df = finder.get_data_frames()[0]
        time.sleep(0.8)
        return df
    except Exception as e:
        print(f'Erro ao coletar {season} {season_type}: {e}', flush=True)
        return None

def get_team_id_map():
    teams = nba_teams_static.get_teams()
    return {t['abbreviation']: t['id'] for t in teams}

def save_season_games(df, season, season_type, conn):
    cursor = conn.cursor()
    is_playoff = 1 if season_type == 'Playoffs' else 0

    # Agrupa por game_id — cada jogo aparece duas vezes (home e away)
    grouped = {}
    for _, row in df.iterrows():
        game_id = row['GAME_ID']
        if game_id not in grouped:
            grouped[game_id] = []
        grouped[game_id].append(row)

    saved = 0
    for game_id, rows in grouped.items():
        if len(rows) != 2:
            continue

        home_rows = [r for r in rows if 'vs.' in str(r['MATCHUP'])]
        away_rows = [r for r in rows if ' @ ' in str(r['MATCHUP'])]

        if not home_rows or not away_rows:
            continue

        home_row = home_rows[0]
        away_row = away_rows[0]

        home_id = int(home_row['TEAM_ID'])
        away_id = int(away_row['TEAM_ID'])
        home_tricode = home_row['TEAM_ABBREVIATION']
        away_tricode = away_row['TEAM_ABBREVIATION']
        home_score = int(home_row['PTS']) if home_row['PTS'] else None
        away_score = int(away_row['PTS']) if away_row['PTS'] else None
        home_win = 1 if home_row['WL'] == 'W' else 0
        game_date = home_row['GAME_DATE']
        total_points = (home_score + away_score) if home_score and away_score else None

        # Salva jogo
        cursor.execute('''
            INSERT OR IGNORE INTO games
            (game_id, game_date, season, season_type,
             home_team_id, away_team_id,
             home_team_tricode, away_team_tricode,
             home_score, away_score,
             home_win, total_points, is_playoff)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            game_id, game_date, season, season_type,
            home_id, away_id,
            home_tricode, away_tricode,
            home_score, away_score,
            home_win, total_points, is_playoff
        ))

        # Salva stats do time home
        for row, is_home in [(home_row, 1), (away_row, 0)]:
            team_id = int(row['TEAM_ID'])
            pts = int(row['PTS']) if row['PTS'] else 0
            fga = int(row['FGA']) if row['FGA'] else 0
            fta = int(row['FTA']) if row['FTA'] else 0
            oreb = int(row['OREB']) if row['OREB'] else 0
            tov = int(row['TOV']) if row['TOV'] else 0
            ts_pct = calc_ts_pct(pts, fga, fta)
            pace = calc_pace(fga, oreb, tov, fta)

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

        saved += 1

    conn.commit()
    return saved

def collect_all():
    init_db()
    conn = get_connection()

    total = len(SEASONS) * len(SEASON_TYPES)
    count = 0

    for season in SEASONS:
        for season_type in SEASON_TYPES:
            count += 1
            print(f'[{count}/{total}] {season} — {season_type}', flush=True)

            df = collect_season(season, season_type)
            if df is not None and not df.empty:
                saved = save_season_games(df, season, season_type, conn)
                print(f'  {saved} jogos salvos.', flush=True)

    conn.close()
    print('Coleta concluída!', flush=True)

if __name__ == '__main__':
    collect_all()