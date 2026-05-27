import tweepy
import os
from dotenv import load_dotenv

load_dotenv()

def get_client():
    client = tweepy.Client(
        consumer_key=os.getenv('TWITTER_API_KEY'),
        consumer_secret=os.getenv('TWITTER_API_SECRET'),
        access_token=os.getenv('TWITTER_ACCESS_TOKEN'),
        access_token_secret=os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
    )
    return client

def post_tweet(text):
    try:
        client = get_client()
        client.create_tweet(text=text)
        print(f'Tweet postado com sucesso!')
    except Exception as e:
        print(f'Erro ao postar tweet: {e}')