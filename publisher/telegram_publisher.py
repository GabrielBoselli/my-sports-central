import os
import asyncio
from telegram import Bot
from dotenv import load_dotenv

load_dotenv()

async def send_message_async(text):
    bot = Bot(token=os.getenv('TELEGRAM_BOT_TOKEN'))
    channel_id = os.getenv('TELEGRAM_CHANNEL_ID')
    await bot.send_message(chat_id=channel_id, text=text)

def post_message(text):
    try:
        asyncio.run(send_message_async(text))
        print('Mensagem enviada com sucesso!')
    except Exception as e:
        print(f'Erro ao enviar mensagem: {e}')