from sports.basketball.nba import get_live_scores, get_boxscore, get_next_game_wait
from sports.basketball.alerts import (
    check_foul_trouble, format_foul_alert,
    check_win_probability, format_win_prob_alert
)
from publisher.formatter import format_score_update, format_game_over, format_executive_summary
from publisher.telegram_publisher import post_message, post_alert
from datetime import datetime, timezone, timedelta
import time
import os
import sqlite3
import subprocess
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ['PYTHONUNBUFFERED'] = '1'

previous_scores = {}
finished_games = []
foul_alerts_sent = set()
win_prob_state = {}
predictions_sent = set()
last_update = None

def daily_update():
    global last_update
    print('Rodando atualização diária...', flush=True)
    try:
        import importlib
        import data.collector as collector
        import data.features as features
        import data.train as train

        collector.collect_all()
        print('Coleta concluída.', flush=True)

        data_path = os.environ.get('DATA_PATH', 'data')
        conn = sqlite3.connect(os.path.join(data_path, 'nba.db'))
        conn.execute('DELETE FROM game_features')
        conn.commit()
        conn.close()

        features.build_features()
        print('Features calculadas.', flush=True)

        train.main()
        print('Modelo retreinado.', flush=True)

        last_update = datetime.now(timezone.utc).date()
        print('Atualização diária concluída!', flush=True)

    except Exception as e:
        print(f'Erro na atualização diária: {e}', flush=True)

def first_run():
    data_path = os.environ.get('DATA_PATH', 'data')
    db_path = os.path.join(data_path, 'nba.db')
    if not os.path.exists(db_path):
        print('Primeira execução — rodando pipeline completo...', flush=True)
        daily_update()

def should_update():
    agora = datetime.now(timezone.utc)
    if agora.hour == 14:
        hoje = agora.date()
        if last_update != hoje:
            return True
    return False

def check_and_post():
    data = get_live_scores()

    if not data:
        print('Sem dados disponíveis.', flush=True)
        return True

    games = data['scoreboard']['games']

    if not games:
        print('Nenhum jogo hoje. Verificando em 1 hora...', flush=True)
        time.sleep(3600)
        return True

    jogos_ativos = [g for g in games if g['gameStatus'] == 2]
    jogos_futuros = [g for g in games if g['gameStatus'] == 1]
    jogos_encerrados = [g for g in games if g['gameStatus'] == 3]

    # Previsões pré-jogo — 1 hora antes
    for game in jogos_futuros:
        game_time_utc = game.get('gameTimeUTC', '')
        game_id = game['gameId']
        try:
            dt = datetime.fromisoformat(game_time_utc.replace('Z', '+00:00'))
            minutos = (dt - datetime.now(timezone.utc)).total_seconds() / 60
            if 55 <= minutos <= 65 and game_id not in predictions_sent:
                predictions_sent.add(game_id)
                print(f'Disparando previsão pré-jogo para {game_id}...', flush=True)
                try:
                    from data.predict import run_predictions
                    run_predictions()
                except Exception as e:
                    print(f'Erro ao gerar previsão: {e}', flush=True)
        except Exception as e:
            print(f'Erro ao checar horário do jogo: {e}', flush=True)

    # Jogos encerrados
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
        else:
            print('Sem jogos hoje. Verificando em 1 hora...', flush=True)
            time.sleep(3600)
        return True

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

        # Win probability
        wp_alert = check_win_probability(game, win_prob_state)
        if wp_alert:
            post_alert(format_win_prob_alert(wp_alert))

        # Foul trouble
        boxscore_data = get_boxscore(game_id)
        if boxscore_data:
            foul_alerts = check_foul_trouble(boxscore_data, game)
            for alert in foul_alerts:
                alert_key = f"{game_id}_{alert['player']}_{alert['fouls']}"
                if alert_key not in foul_alerts_sent:
                    foul_alerts_sent.add(alert_key)
                    post_alert(format_foul_alert(alert))

    return True

if __name__ == '__main__':
    print('🏆 My Sports Central iniciado!', flush=True)
    first_run()
    post_message('🏆 My Sports Central está monitorando jogos ao vivo!')
    while True:
        if should_update():
            daily_update()
        check_and_post()
        time.sleep(30)