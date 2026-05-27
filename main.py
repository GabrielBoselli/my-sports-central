from sports.basketball.nba import get_live_scores
from publisher.formatter import format_score_update
from publisher.telegram_publisher import post_message
import time

previous_scores = {}

def check_and_post():
    data = get_live_scores()

    if not data:
        print('Sem dados disponíveis.')
        return

    games = data['scoreboard']['games']

    if not games:
        print('Nenhum jogo acontecendo agora.')
        return

    for game in games:
        game_id = game['gameId']
        home_score = game['homeTeam']['score']
        away_score = game['awayTeam']['score']
        current_score = (home_score, away_score)

        if game_id not in previous_scores:
            previous_scores[game_id] = current_score
            message = format_score_update(game)
            post_message(message)
            print('Primeiro update postado!')
        elif current_score != previous_scores[game_id]:
            previous_scores[game_id] = current_score
            message = format_score_update(game)
            post_message(message)
            print('Placar mudou, update postado!')
        else:
            print('Placar não mudou, aguardando...')

if __name__ == '__main__':
    print('🏆 My Sports Central iniciado!')
    post_message('🏆 My Sports Central está monitorando jogos ao vivo!')
    while True:
        check_and_post()
        time.sleep(30)
