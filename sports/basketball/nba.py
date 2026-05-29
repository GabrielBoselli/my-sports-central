from nba_api.live.nba.endpoints import scoreboard
from nba_api.stats.library.parameters import LeagueID
from nba_api.live.nba.endpoints import boxscore as boxscore_endpoint
from datetime import datetime, timezone


headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://www.nba.com/'
}

def get_live_scores():
    try:
        games = scoreboard.ScoreBoard(proxy=None, headers=headers)
        data = games.get_dict()
        return data
    except Exception as e:
        print(f"Erro ao buscar jogos: {e}")
        return None
    
def get_boxscore(game_id):
    try:
        box = boxscore_endpoint.BoxScore(game_id=game_id)
        return box.get_dict()
    except Exception as e:
        print(f'Erro ao buscar boxscore: {e}')
        return None
    

def get_next_game_wait(games):
    agora = datetime.now(timezone.utc)
    
    jogos_futuros = [g for g in games if g['gameStatus'] == 1]
    
    if not jogos_futuros:
        return None
    # Pega o horário do próximo jogo
    proximo = min(jogos_futuros, key=lambda g: g['gameTimeUTC'])
    horario_jogo = datetime.fromisoformat(
        proximo['gameTimeUTC'].replace('Z', '+00:00')
    )
    # Calcula quantos segundos faltam (menos 30 minutos)
    segundos = (horario_jogo - agora).total_seconds() - 1800
    return max(segundos, 0)
