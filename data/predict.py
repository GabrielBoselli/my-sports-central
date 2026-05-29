import sqlite3
import os
import pickle
import pandas as pd
from datetime import datetime, timezone, timedelta
from nba_api.stats.static import teams as nba_teams_static
from sports.basketball.nba import get_live_scores

DATA_PATH = os.environ.get('DATA_PATH', os.path.dirname(__file__))
DB_PATH = os.path.join(DATA_PATH, 'nba.db')

FEATURES = [
    'home_last10_winrate', 'away_last10_winrate',
    'home_last10_net_rating', 'away_last10_net_rating',
    'home_last10_avg_pts', 'away_last10_avg_pts',
    'home_last10_avg_pts_allowed', 'away_last10_avg_pts_allowed',
    'home_last10_ts_pct', 'away_last10_ts_pct',
    'home_last10_pace', 'away_last10_pace',
    'home_streak', 'away_streak',
    'home_rest_days', 'away_rest_days',
    'home_back_to_back', 'away_back_to_back',
    'h2h_last5_home_wins', 'h2h_last5_away_wins',
    'h2h_avg_total_pts',
]

def load_models():
    base = os.environ.get('DATA_PATH', os.path.dirname(__file__))
    with open(os.path.join(base, 'model_result.pkl'), 'rb') as f:
        model_result = pickle.load(f)
    with open(os.path.join(base, 'model_over.pkl'), 'rb') as f:
        model_over = pickle.load(f)
    return model_result, model_over

def get_connection():
    return sqlite3.connect(DB_PATH)

def get_team_id_by_tricode(tricode):
    all_teams = nba_teams_static.get_teams()
    for t in all_teams:
        if t['abbreviation'] == tricode:
            return t['id']
    return None

def get_last_game_date(cursor, team_id):
    cursor.execute('''
        SELECT g.game_date FROM games g
        JOIN team_game_stats tgs ON g.game_id = tgs.game_id
        WHERE tgs.team_id = ?
        ORDER BY g.game_date DESC, g.game_id DESC
        LIMIT 1
    ''', (team_id,))
    row = cursor.fetchone()
    return row[0] if row else None

def calc_rest_days(cursor, team_id, game_date_utc):
    last_date_str = get_last_game_date(cursor, team_id)
    if not last_date_str:
        return 2
    from datetime import datetime
    for fmt in ['%b %d, %Y', '%B %d, %Y', '%b %d,%Y']:
        try:
            last_date = datetime.strptime(last_date_str.strip(), fmt)
            diff = (game_date_utc - last_date).days
            return max(0, min(diff, 30))
        except:
            continue
    return 2

def build_game_features(cursor, home_id, away_id, game_date_utc):
    from data.features import calc_team_features, calc_h2h_features

    # Usa o game_id mais recente como referência
    cursor.execute('''
        SELECT MAX(game_id) FROM games
    ''')
    last_game_id = cursor.fetchone()[0]
    fake_game_id = str(int(last_game_id) + 1)

    home_feats = calc_team_features(cursor, home_id, fake_game_id, 'home')
    away_feats = calc_team_features(cursor, away_id, fake_game_id, 'away')
    h2h_feats = calc_h2h_features(cursor, home_id, away_id, fake_game_id)

    # Sobrescreve rest days com o valor real baseado na data do jogo
    home_rest = calc_rest_days(cursor, home_id, game_date_utc)
    away_rest = calc_rest_days(cursor, away_id, game_date_utc)

    return {
        'home_last10_winrate': home_feats['home_last10_winrate'],
        'away_last10_winrate': away_feats['away_last10_winrate'],
        'home_last10_net_rating': home_feats['home_last10_net_rating'],
        'away_last10_net_rating': away_feats['away_last10_net_rating'],
        'home_last10_avg_pts': home_feats['home_last10_avg_pts'],
        'away_last10_avg_pts': away_feats['away_last10_avg_pts'],
        'home_last10_avg_pts_allowed': home_feats['home_last10_avg_pts_allowed'],
        'away_last10_avg_pts_allowed': away_feats['away_last10_avg_pts_allowed'],
        'home_last10_ts_pct': home_feats['home_last10_ts_pct'],
        'away_last10_ts_pct': away_feats['away_last10_ts_pct'],
        'home_last10_pace': home_feats['home_last10_pace'],
        'away_last10_pace': away_feats['away_last10_pace'],
        'home_streak': home_feats['home_streak'],
        'away_streak': away_feats['away_streak'],
        'home_rest_days': home_rest,
        'away_rest_days': away_rest,
        'home_back_to_back': 1 if home_rest <= 1 else 0,
        'away_back_to_back': 1 if away_rest <= 1 else 0,
        'h2h_last5_home_wins': h2h_feats['h2h_last5_home_wins'],
        'h2h_last5_away_wins': h2h_feats['h2h_last5_away_wins'],
        'h2h_avg_total_pts': h2h_feats['h2h_avg_total_pts'],
    }

def get_top_factors(features):
    factors = []

    home_net = features['home_last10_net_rating']
    away_net = features['away_last10_net_rating']
    if abs(home_net - away_net) > 5:
        better = 'mandante' if home_net > away_net else 'visitante'
        factors.append(f'Net rating superior do {better}')

    home_rest = features['home_rest_days']
    away_rest = features['away_rest_days']
    if abs(home_rest - away_rest) >= 2:
        more_rest = 'mandante' if home_rest > away_rest else 'visitante'
        factors.append(f'Vantagem de descanso do {more_rest} ({max(home_rest, away_rest)} dias)')

    if features['home_back_to_back'] or features['away_back_to_back']:
        who = 'Mandante' if features['home_back_to_back'] else 'Visitante'
        factors.append(f'{who} em back-to-back')

    home_wr = features['home_last10_winrate']
    away_wr = features['away_last10_winrate']
    if abs(home_wr - away_wr) > 0.2:
        better = 'mandante' if home_wr > away_wr else 'visitante'
        factors.append(f'Melhor forma recente do {better}')

    h2h_home = features['h2h_last5_home_wins']
    h2h_away = features['h2h_last5_away_wins']
    if h2h_home + h2h_away > 0:
        if h2h_home > h2h_away + 1:
            factors.append(f'Vantagem no H2H recente ({h2h_home}x{h2h_away})')
        elif h2h_away > h2h_home + 1:
            factors.append(f'Visitante domina H2H recente ({h2h_away}x{h2h_home})')

    return factors[:3] if factors else ['Jogo equilibrado']

def format_prediction(game, result_prob, over_prob, features):
    home = game['homeTeam']
    away = game['awayTeam']

    home_win_pct = round(result_prob * 100)
    away_win_pct = 100 - home_win_pct
    over_pct = round(over_prob * 100)
    under_pct = 100 - over_pct

    favorite = f"{home['teamCity']} {home['teamName']}" if home_win_pct >= 50 else f"{away['teamCity']} {away['teamName']}"
    fav_pct = max(home_win_pct, away_win_pct)

    over_under = 'OVER 224' if over_pct >= 50 else 'UNDER 224'
    ou_pct = max(over_pct, under_pct)

    factors = get_top_factors(features)
    factors_text = '\n'.join([f'  • {f}' for f in factors])

    game_label = game.get('gameLabel', '')
    series_text = game.get('seriesText', '')

    header = f"{game_label} — {series_text}\n" if game_label else ''

    # Horário em Brasília (UTC-3)
    game_time_utc = game.get('gameTimeUTC', '')
    horario = ''
    if game_time_utc:
        try:
            dt = datetime.fromisoformat(game_time_utc.replace('Z', '+00:00'))
            dt_br = dt.astimezone(timezone(timedelta(hours=-3)))
            horario = f"🕐 {dt_br.strftime('%H:%M')} (horário de Brasília)\n"
        except:
            pass

    return (
        f"🔮 PREVISÃO PRÉ-JOGO\n"
        f"{'─' * 28}\n"
        f"{header}"
        f"🏀 {away['teamCity']} {away['teamName']} @ "
        f"{home['teamCity']} {home['teamName']}\n"
        f"{horario}\n"
        f"📊 Resultado\n"
        f"  → {favorite} — {fav_pct}% de chance\n\n"
        f"🎯 Total de pontos\n"
        f"  → {over_under} — {ou_pct}% de confiança\n\n"
        f"🔍 Principais fatores\n"
        f"{factors_text}\n\n"
        f"⚠️ Modelo experimental — use como análise"
    )

def run_predictions():
    print('Carregando modelos...', flush=True)
    model_result, model_over = load_models()

    data = get_live_scores()
    if not data:
        print('Sem dados disponíveis.', flush=True)
        return

    games = data['scoreboard']['games']
    jogos_futuros = [g for g in games if g['gameStatus'] == 1]

    if not jogos_futuros:
        print('Sem jogos futuros hoje.', flush=True)
        return

    conn = get_connection()
    cursor = conn.cursor()

    from publisher.telegram_publisher import post_alert

    for game in jogos_futuros:
        home_tricode = game['homeTeam']['teamTricode']
        away_tricode = game['awayTeam']['teamTricode']

        home_id = get_team_id_by_tricode(home_tricode)
        away_id = get_team_id_by_tricode(away_tricode)

        if not home_id or not away_id:
            print(f'Time não encontrado: {home_tricode} ou {away_tricode}', flush=True)
            continue

        game_time_utc = game.get('gameTimeUTC', '')
        try:
            game_date = datetime.fromisoformat(game_time_utc.replace('Z', '+00:00')).replace(tzinfo=None)
        except:
            game_date = datetime.utcnow()

        print(f'Gerando previsão: {away_tricode} @ {home_tricode}', flush=True)

        features = build_game_features(cursor, home_id, away_id, game_date)
        X = pd.DataFrame([features])[FEATURES]

        result_prob = model_result.predict_proba(X)[0][1]
        over_prob = model_over.predict_proba(X)[0][1]

        message = format_prediction(game, result_prob, over_prob, features)
        print(message, flush=True)
        post_alert(message)
        print(f'Previsão postada para {away_tricode} @ {home_tricode}', flush=True)

    conn.close()

if __name__ == '__main__':
    run_predictions()