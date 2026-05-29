import os
import asyncio
from telegram import Bot
from dotenv import load_dotenv

load_dotenv()

async def send_message_async(text, channel):
    bot = Bot(token=os.getenv('TELEGRAM_BOT_TOKEN'))
    await bot.send_message(chat_id=channel, text=text)

def post_message(text):
    try:
        asyncio.run(send_message_async(text, os.getenv('TELEGRAM_CHANNEL_ID')))
        print('Mensagem enviada com sucesso!')
    except Exception as e:
        print(f'Erro ao enviar mensagem: {e}')

def post_alert(text):
    try:
        asyncio.run(send_message_async(text, os.getenv('TELEGRAM_ALERTS_CHANNEL_ID')))
        print('Alerta enviado com sucesso!')
    except Exception as e:
        print(f'Erro ao enviar alerta: {e}')