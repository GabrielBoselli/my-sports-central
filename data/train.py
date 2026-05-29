import sqlite3
import os
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, brier_score_loss
from sklearn.calibration import CalibratedClassifierCV
from xgboost import XGBClassifier
import pickle

DB_PATH = os.path.join(os.path.dirname(__file__), 'nba.db')

FEATURES = [
    'home_last10_winrate', 'away_last10_winrate',
    'home_last10_net_rating', 'away_last10_net_rating',
    'home_last10_avg_pts', 'away_last10_avg_pts',
    'home_last10_avg_pts_allowed', 'away_last10_avg_pts_allowed',
    'home_last10_ts_pct', 'away_last10_ts_pct',
    'home_last10_pace', 'away_last10_pace',
    'home_streak', 'away_streak',
    'home_rest_days', 'away_rest_days',
    'home_back_to_back', 'away_back_to_back',
    'h2h_last5_home_wins', 'h2h_last5_away_wins',
    'h2h_avg_total_pts',
]

def load_data():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query('''
        SELECT * FROM game_features
        WHERE home_win IS NOT NULL
          AND over_224 IS NOT NULL
    ''', conn)
    conn.close()
    return df

def train_model(df, target, model_name):
    X = df[FEATURES]
    y = df[target]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, shuffle=True
    )

    base_model = XGBClassifier(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        eval_metric='logloss',
        random_state=42,
        verbosity=0
    )

    # Calibração melhora as probabilidades
    model = CalibratedClassifierCV(base_model, cv=5, method='isotonic')
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    acc = accuracy_score(y_test, y_pred)
    brier = brier_score_loss(y_test, y_prob)

    print(f'\n--- {model_name} ---')
    print(f'Accuracy:    {acc:.4f} ({acc*100:.1f}%)')
    print(f'Brier Score: {brier:.4f} (menor = melhor, 0.25 = random)')

    model_path = os.path.join(os.path.dirname(__file__), f'{model_name}.pkl')
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    print(f'Modelo salvo em data/{model_name}.pkl')

    return model

def main():
    print('Carregando dados...', flush=True)
    df = load_data()
    print(f'{len(df)} jogos carregados.', flush=True)

    train_model(df, 'home_win', 'model_result')
    train_model(df, 'over_224', 'model_over')

if __name__ == '__main__':
    main()