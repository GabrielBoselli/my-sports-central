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