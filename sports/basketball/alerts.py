import re
import math


def parse_game_clock(clock_str):
    if not clock_str:
        return 0.0
    match = re.match(r'PT(\d+)M([\d.]+)S', clock_str)
    if not match:
        return 0.0
    minutes = int(match.group(1))
    seconds = float(match.group(2))
    return minutes + seconds / 60


def calc_win_probability(score_diff, minutes_remaining):
    if minutes_remaining <= 0:
        return 1.0 if score_diff > 0 else 0.0
    z = score_diff / (2.5 * math.sqrt(minutes_remaining))
    prob = 0.5 + 0.5 * (z / (1 + abs(z)))
    return max(0.02, min(0.98, prob))


def check_foul_trouble(boxscore_data, game):
    alerts = []

    home = boxscore_data['game']['homeTeam']
    away = boxscore_data['game']['awayTeam']

    period = game.get('period', 0)

    for team_data in [home, away]:
        team_name = f"{team_data['teamCity']} {team_data['teamName']}"

        for player in team_data['players']:
            stats = player['statistics']

            if stats['minutesCalculated'] == 'PT00M00S':
                continue

            fouls = stats['foulsPersonal']
            name = player['name']

            if (period <= 2 and fouls >= 3) or (period > 2 and fouls >= 5):
                alerts.append({
                    'player': name,
                    'team': team_name,
                    'fouls': fouls,
                    'period': period
                })

    return alerts


def format_foul_alert(alert):
    period_label = f"Q{alert['period']}"
    limit = 6
    remaining = limit - alert['fouls']

    return (
        f"⚠️ FOUL TROUBLE\n\n"
        f"🏀 {alert['team']}\n"
        f"👤 {alert['player']}\n"
        f"🚨 {alert['fouls']} faltas no {period_label} "
        f"— resta {remaining} pra foulear out\n\n"
        f"📉 Risco de impacto no tempo de quadra"
    )


def check_win_probability(game, prev_probs):
    period = game.get('period', 0)
    clock = game.get('gameClock', '')

    if period == 0 or period > 4:
        return None

    minutes_in_period = parse_game_clock(clock)
    periods_remaining = 4 - period
    total_minutes = minutes_in_period + (periods_remaining * 12)

    home_score = game['homeTeam']['score']
    away_score = game['awayTeam']['score']
    score_diff = home_score - away_score

    home_prob = calc_win_probability(score_diff, total_minutes)
    away_prob = 1 - home_prob

    game_id = game['gameId']
    prev = prev_probs.get(game_id)

    prev_probs[game_id] = {
        'home_prob': home_prob,
        'away_prob': away_prob
    }

    if prev is None:
        return None

    home_diff = abs(home_prob - prev['home_prob'])
    if home_diff >= 0.15 and total_minutes > 1:
        leading_team = game['homeTeam'] if score_diff > 0 else game['awayTeam']
        trailing_team = game['awayTeam'] if score_diff > 0 else game['homeTeam']
        leading_prob = home_prob if score_diff > 0 else away_prob

        return {
            'leading_team': f"{leading_team['teamCity']} {leading_team['teamName']}",
            'trailing_team': f"{trailing_team['teamCity']} {trailing_team['teamName']}",
            'leading_prob': leading_prob,
            'score_diff': abs(score_diff),
            'minutes_remaining': round(total_minutes, 1),
            'period': period
        }

    return None


def format_win_prob_alert(alert):
    prob_pct = round(alert['leading_prob'] * 100)
    return (
        f"📊 VIRADA EM ANDAMENTO\n\n"
        f"📈 {alert['leading_team']} assumiu o controle\n"
        f"🎯 Probabilidade de vitória: {prob_pct}%\n"
        f"🏀 Diferença: {alert['score_diff']} pontos\n"
        f"⏱ {alert['minutes_remaining']} min restantes — Q{alert['period']}\n\n"
        f"📉 {alert['trailing_team']} precisa reagir"
    )