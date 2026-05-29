from sports.basketball.nba import get_live_scores, get_boxscore, get_next_game_wait
from publisher.formatter import format_score_update, format_game_over, format_executive_summary
from publisher.telegram_publisher import post_message
import time
import os

os.environ['PYTHONUNBUFFERED'] = '1'

previous_scores = {}
finished_games = []

def check_and_post():
    data = get_live_scores()

    if not data:
        print('Sem dados disponíveis.', flush=True)
        return False

    games = data['scoreboard']['games']

    if not games:
        print('Nenhum jogo hoje.', flush=True)
        return False

    jogos_ativos = [g for g in games if g['gameStatus'] == 2]
    jogos_futuros = [g for g in games if g['gameStatus'] == 1]
    jogos_encerrados = [g for g in games if g['gameStatus'] == 3]

    # Processa jogos encerrados sempre
    for game in jogos_encerrados:
        game_id = game['gameId']
        if game_id not in finished_games:
            print(f'Jogo encerrado: {game_id}', flush=True)
            finished_games.append(game_id)
            message = format_game_over(game)
            post_message(message)
            boxscore_data = get_boxscore(game_id)
            print(f'Boxscore retornou: {boxscore_data is not None}', flush=True)
            if boxscore_data:
                summary = format_executive_summary(game, boxscore_data)
                post_message(summary)
                print('Resumo executivo postado.', flush=True)

    if not jogos_ativos:
        if jogos_futuros:
            espera = get_next_game_wait(games)
            if espera and espera > 0:
                horas = int(espera // 3600)
                minutos = int((espera % 3600) // 60)
                print(f'Próximo jogo em {horas}h {minutos}min, aguardando...', flush=True)
                time.sleep(espera)
            return True
        else:
            print('Todos os jogos encerraram.', flush=True)
            return False

    for game in games:
        game_id = game['gameId']
        home_score = game['homeTeam']['score']
        away_score = game['awayTeam']['score']
        current_score = (home_score, away_score)
        game_status = game['gameStatus']

        if game_status != 2:
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
            print('Placar não mudou, aguardando...', flush=True)

    return True

if __name__ == '__main__':
    print('🏆 My Sports Central iniciado!', flush=True)
    post_message('🏆 My Sports Central está monitorando jogos ao vivo!')
    while True:
        continuar = check_and_post()
        if not continuar:
            print('Encerrando bot — sem jogos ativos.', flush=True)
            break
        time.sleep(30)