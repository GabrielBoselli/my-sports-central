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


def format_game_over(game):
    home = game['homeTeam']
    away = game['awayTeam']
    home_leader = game['gameLeaders']['homeLeaders']
    away_leader = game['gameLeaders']['awayLeaders']

    # Descobre o vencedor
    if home['score'] > away['score']:
        winner = f"{home['teamCity']} {home['teamName']}"
    else:
        winner = f"{away['teamCity']} {away['teamName']}"

    # Descobre o MVP (maior pontuador)
    if home_leader['points'] >= away_leader['points']:
        mvp = home_leader
    else:
        mvp = away_leader

    message = (
        f"🏁 FIM DE JOGO!\n\n"
        f"🏀 {away['teamCity']} {away['teamName']} {away['score']} x "
        f"{home['score']} {home['teamCity']} {home['teamName']}\n"
        f"🏆 {game['gameLabel']} — {game['seriesText']}\n\n"
        f"🎯 Vencedor: {winner}\n\n"
        f"⭐ Destaque da partida:\n"
        f"{mvp['name']} — {mvp['points']}pts "
        f"{mvp['rebounds']}reb {mvp['assists']}ast"
    )

    return message