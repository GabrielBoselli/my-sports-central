import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'nba.db')

def get_connection():
    return sqlite3.connect(DB_PATH)

def parse_date(date_str):
    if not date_str:
        return None
    date_str = date_str.strip()
    for fmt in ['%b %d, %Y', '%B %d, %Y', '%b %d,%Y', '%Y-%m-%d']:
        try:
            return datetime.strptime(date_str, fmt)
        except:
            continue
    return None

def get_team_last_n_games(cursor, team_id, before_game_id, n=10):
    cursor.execute('''
        SELECT g.game_id, g.game_date, g.home_win,
               g.home_team_id, g.away_team_id,
               tgs.pts, tgs.is_home
        FROM games g
        JOIN team_game_stats tgs ON g.game_id = tgs.game_id
        WHERE tgs.team_id = ?
          AND g.game_id != ?
          AND g.game_id < ?
        ORDER BY g.game_id DESC
        LIMIT ?
    ''', (team_id, before_game_id, before_game_id, n))
    return cursor.fetchall()

def get_opponent_pts(cursor, game_id, team_id):
    cursor.execute('''
        SELECT pts FROM team_game_stats
        WHERE game_id = ? AND team_id != ?
    ''', (game_id, team_id))
    row = cursor.fetchone()
    return row[0] if row else None

def calc_team_features(cursor, team_id, before_game_id, prefix):
    games = get_team_last_n_games(cursor, team_id, before_game_id, n=10)

    if not games:
        return {
            f'{prefix}_last10_winrate': 0.5,
            f'{prefix}_last10_net_rating': 0.0,
            f'{prefix}_last10_avg_pts': 110.0,
            f'{prefix}_last10_avg_pts_allowed': 110.0,
            f'{prefix}_last10_ts_pct': 0.55,
            f'{prefix}_last10_pace': 45.0,
            f'{prefix}_streak': 0,
            f'{prefix}_rest_days': 2,
            f'{prefix}_back_to_back': 0,
        }

    wins = 0
    pts_list = []
    pts_allowed_list = []
    ts_list = []
    pace_list = []
    dates = []

    for row in games:
        game_id, game_date, home_win, home_team_id, away_team_id, pts, is_home = row

        is_winner = (is_home == 1 and home_win == 1) or (is_home == 0 and home_win == 0)
        if is_winner:
            wins += 1

        pts_list.append(pts)

        opp_pts = get_opponent_pts(cursor, game_id, team_id)
        if opp_pts:
            pts_allowed_list.append(opp_pts)

        cursor.execute('''
            SELECT ts_pct, pace FROM team_game_stats
            WHERE game_id = ? AND team_id = ?
        ''', (game_id, team_id))
        stats = cursor.fetchone()
        if stats:
            ts_list.append(stats[0])
            pace_list.append(stats[1])

        parsed = parse_date(game_date)
        if parsed:
            dates.append(parsed)

    n = len(games)
    winrate = wins / n
    avg_pts = sum(pts_list) / len(pts_list) if pts_list else 110.0
    avg_pts_allowed = sum(pts_allowed_list) / len(pts_allowed_list) if pts_allowed_list else 110.0
    net_rating = avg_pts - avg_pts_allowed
    avg_ts = sum(ts_list) / len(ts_list) if ts_list else 0.55
    avg_pace = sum(pace_list) / len(pace_list) if pace_list else 45.0

    # Streak
    streak = 0
    last_result = None
    for row in games:
        game_id, game_date, home_win, home_team_id, away_team_id, pts, is_home = row
        is_winner = (is_home == 1 and home_win == 1) or (is_home == 0 and home_win == 0)
        if last_result is None:
            last_result = is_winner
            streak = 1 if is_winner else -1
        elif is_winner == last_result:
            streak = streak + 1 if is_winner else streak - 1
        else:
            break

    # Rest days
    cursor.execute('''
        SELECT g.game_date FROM games g
        JOIN team_game_stats tgs ON g.game_id = tgs.game_id
        WHERE tgs.team_id = ? AND g.game_id = ?
    ''', (team_id, before_game_id))
    current_game_row = cursor.fetchone()
    rest_days = 2
    back_to_back = 0
    if current_game_row and dates:
        current_date = parse_date(current_game_row[0])
        last_game_date = dates[0]
        if current_date and last_game_date:
            diff = (current_date - last_game_date).days
            rest_days = max(0, min(diff, 30))
            back_to_back = 1 if diff <= 1 else 0

    return {
        f'{prefix}_last10_winrate': round(winrate, 4),
        f'{prefix}_last10_net_rating': round(net_rating, 2),
        f'{prefix}_last10_avg_pts': round(avg_pts, 2),
        f'{prefix}_last10_avg_pts_allowed': round(avg_pts_allowed, 2),
        f'{prefix}_last10_ts_pct': round(avg_ts, 4),
        f'{prefix}_last10_pace': round(avg_pace, 2),
        f'{prefix}_streak': streak,
        f'{prefix}_rest_days': rest_days,
        f'{prefix}_back_to_back': back_to_back,
    }

def calc_h2h_features(cursor, home_team_id, away_team_id, before_game_id, n=5, exclude_season=None):
    season_filter = "AND g.season != ?" if exclude_season else ""
    params = [home_team_id, away_team_id, away_team_id, home_team_id,
              before_game_id, before_game_id]
    if exclude_season:
        params.append(exclude_season)
    params.append(n)

    cursor.execute(f'''
        SELECT g.home_win, g.home_score, g.away_score, g.home_team_id
        FROM games g
        WHERE ((g.home_team_id = ? AND g.away_team_id = ?)
            OR (g.home_team_id = ? AND g.away_team_id = ?))
          AND g.game_id != ?
          AND g.game_id < ?
          {season_filter}
        ORDER BY g.game_id DESC
        LIMIT ?
    ''', params)
    rows = cursor.fetchall()

    if not rows:
        return {
            'h2h_last5_home_wins': 2,
            'h2h_last5_away_wins': 2,
            'h2h_avg_total_pts': 220.0,
        }

    home_wins = 0
    away_wins = 0
    total_pts = []

    for home_win, home_score, away_score, db_home_id in rows:
        # Conta vitória do ponto de vista do home_team_id da query
        if db_home_id == home_team_id:
            won = home_win == 1
        else:
            won = home_win == 0

        if won:
            home_wins += 1
        else:
            away_wins += 1

        if home_score and away_score:
            total_pts.append(home_score + away_score)

    avg_total = sum(total_pts) / len(total_pts) if total_pts else 220.0

    return {
        'h2h_last5_home_wins': home_wins,
        'h2h_last5_away_wins': away_wins,
        'h2h_avg_total_pts': round(avg_total, 2),
    }

def build_features():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT game_id, game_date, home_team_id, away_team_id,
               home_win, total_points, is_playoff,
               home_score, away_score
        FROM games
        WHERE home_team_id IS NOT NULL
          AND away_team_id IS NOT NULL
          AND home_win IS NOT NULL
          AND total_points IS NOT NULL
        ORDER BY game_id ASC
    ''')
    games = cursor.fetchall()

    print(f'Calculando features para {len(games)} jogos...', flush=True)

    inserted = 0
    for i, game in enumerate(games):
        game_id, game_date, home_id, away_id, home_win, total_pts, is_playoff, home_score, away_score = game

        cursor.execute('SELECT 1 FROM game_features WHERE game_id = ?', (game_id,))
        if cursor.fetchone():
            continue

        home_feats = calc_team_features(cursor, home_id, game_id, 'home')
        away_feats = calc_team_features(cursor, away_id, game_id, 'away')
        h2h_feats = calc_h2h_features(cursor, home_id, away_id, game_id)

        over_224 = 1 if total_pts > 224 else 0

        cursor.execute('''
            INSERT OR IGNORE INTO game_features (
                game_id, home_team_id, away_team_id,
                home_last10_winrate, away_last10_winrate,
                home_last10_net_rating, away_last10_net_rating,
                home_last10_avg_pts, away_last10_avg_pts,
                home_last10_avg_pts_allowed, away_last10_avg_pts_allowed,
                home_last10_ts_pct, away_last10_ts_pct,
                home_last10_pace, away_last10_pace,
                home_streak, away_streak,
                home_rest_days, away_rest_days,
                home_back_to_back, away_back_to_back,
                h2h_last5_home_wins, h2h_last5_away_wins,
                h2h_avg_total_pts,
                playoff_game_number, home_series_wins, away_series_wins,
                home_win, total_points, over_224
            ) VALUES (
                ?, ?, ?,
                ?, ?,
                ?, ?,
                ?, ?,
                ?, ?,
                ?, ?,
                ?, ?,
                ?, ?,
                ?, ?,
                ?, ?,
                ?, ?,
                ?,
                ?, ?, ?,
                ?, ?, ?
            )
        ''', (
            game_id, home_id, away_id,
            home_feats['home_last10_winrate'], away_feats['away_last10_winrate'],
            home_feats['home_last10_net_rating'], away_feats['away_last10_net_rating'],
            home_feats['home_last10_avg_pts'], away_feats['away_last10_avg_pts'],
            home_feats['home_last10_avg_pts_allowed'], away_feats['away_last10_avg_pts_allowed'],
            home_feats['home_last10_ts_pct'], away_feats['away_last10_ts_pct'],
            home_feats['home_last10_pace'], away_feats['away_last10_pace'],
            home_feats['home_streak'], away_feats['away_streak'],
            home_feats['home_rest_days'], away_feats['away_rest_days'],
            home_feats['home_back_to_back'], away_feats['away_back_to_back'],
            h2h_feats['h2h_last5_home_wins'], h2h_feats['h2h_last5_away_wins'],
            h2h_feats['h2h_avg_total_pts'],
            0, 0, 0,
            home_win, total_pts, over_224
        ))

        inserted += 1
        if i % 100 == 0:
            conn.commit()
            print(f'[{i}/{len(games)}] {inserted} features calculadas...', flush=True)

    conn.commit()
    conn.close()
    print(f'Concluído! {inserted} registros inseridos na game_features.', flush=True)

if __name__ == '__main__':
    build_features()