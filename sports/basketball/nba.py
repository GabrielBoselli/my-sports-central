from nba_api.live.nba.endpoints import scoreboard
from nba_api.stats.library.parameters import LeagueID
from nba_api.live.nba.endpoints import boxscore as boxscore_endpoint

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