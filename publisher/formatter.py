def format_score_update(game):
    home = game['homeTeam']
    away = game['awayTeam']
    status = game['gameStatusText']
    home_leader = game['gameLeaders']['homeLeaders']
    away_leader = game['gameLeaders']['awayLeaders']

    tweet = (
        f"🏀 {away['teamCity']} {away['teamName']} {away['score']} x "
        f"{home['score']} {home['teamCity']} {home['teamName']}\n"
        f"⏱ {status}\n"
        f"🏆 {game['gameLabel']} — {game['seriesText']}\n\n"
        f"⭐ {home['teamTricode']}: {home_leader['name']} "
        f"{home_leader['points']}pts {home_leader['rebounds']}reb {home_leader['assists']}ast\n"
        f"⭐ {away['teamTricode']}: {away_leader['name']} "
        f"{away_leader['points']}pts {away_leader['rebounds']}reb {away_leader['assists']}ast"
    )

    return tweet