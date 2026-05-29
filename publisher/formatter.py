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


def format_executive_summary(game, boxscore_data):
    home = game['homeTeam']
    away = game['awayTeam']

    def format_quarters(team):
        periods = team['periods']
        quarters = [str(p['score']) for p in periods if p['score'] > 0]
        return ' | '.join(quarters)

    def get_top_players(team_data):
        players = team_data['players']
        valid = [p for p in players if p['statistics']['points'] is not None]
        sorted_players = sorted(
            valid,
            key=lambda x: x['statistics']['points'],
            reverse=True
        )
        return sorted_players[:5]

    home_players = get_top_players(
        boxscore_data['game']['homeTeam']
    )
    away_players = get_top_players(
        boxscore_data['game']['awayTeam']
    )

    def format_player_line(p):
        s = p['statistics']
        name = p['name']
        return (
            f"  {name}: {s['points']}pts "
            f"{s['reboundsTotal']}reb "
            f"{s['assists']}ast "
            f"{s['steals']}stl "
            f"{s['blocks']}blk"
        )

    home_lines = '\n'.join([format_player_line(p) for p in home_players])
    away_lines = '\n'.join([format_player_line(p) for p in away_players])

    message = (
        f"📊 RESUMO EXECUTIVO\n"
        f"{'─' * 30}\n\n"
        f"🏀 {away['teamCity']} {away['teamName']} "
        f"{away['score']} x {home['score']} "
        f"{home['teamCity']} {home['teamName']}\n\n"
        f"📈 PONTOS POR QUARTO\n"
        f"{away['teamTricode']}: {format_quarters(away)}\n"
        f"{home['teamTricode']}: {format_quarters(home)}\n\n"
        f"⭐ TOP 5 — {home['teamCity']} {home['teamName']}\n"
        f"{home_lines}\n\n"
        f"⭐ TOP 5 — {away['teamCity']} {away['teamName']}\n"
        f"{away_lines}"
    )

    return message