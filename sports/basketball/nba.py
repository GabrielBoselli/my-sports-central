from nba_api.live.nba.endpoints import scoreboard
from nba_api.stats.library.parameters import LeagueID

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