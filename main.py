from publisher.telegram_publisher import post_message
from sports.basketball.nba import get_live_scores, get_boxscore
from publisher.formatter import format_score_update, format_game_over, format_executive_summary
import time

previous_scores = {}
finished_games = []  

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
        game_status = game['gameStatus']


        if game_status == 3:
            if game_id not in finished_games:
                finished_games.append(game_id)
                message = format_game_over(game)
                post_message(message)


            boxscore_data = get_boxscore(game_id)
            if boxscore_data:
                summary = format_executive_summary(game, boxscore_data)
                post_message(summary)
                print('Resumo executivo postado.')
            continue



        if game_id not in previous_scores:
            previous_scores[game_id] = current_score
            message = format_score_update(game)
            post_message(message)
        elif current_score != previous_scores[game_id]:
            previous_scores[game_id] = current_score
            message = format_score_update(game)
            post_message(message)
        else:
            print('Placar não mudou, aguardando...')

if __name__ == '__main__':
    print('🏆 My Sports Central iniciado!')
    post_message('🏆 My Sports Central está monitorando jogos ao vivo!')
    while True:
        check_and_post()
        time.sleep(30)