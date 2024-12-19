from typing import Final
import os
from dotenv import load_dotenv
from discord import Intents, Client, Message, File
from telethon import TelegramClient, events
import asyncio
import io

# Load environment variables
load_dotenv()
DISCORD_TOKEN: Final[str] = os.getenv('DISCORD_TOKEN')
TELEGRAM_HASH: Final[str] = os.getenv('TELEGRAM_HASH')
API_ID: Final[int] = int(os.getenv('API_ID', '25713302'))  # Use environment variable, fallback to hardcoded value

# Set up clients
intents = Intents.default()
intents.message_content = True
discord_client = Client(intents=intents)
telegram_client = TelegramClient('bob', API_ID, TELEGRAM_HASH)

@discord_client.event
async def on_ready():
    print(f'{discord_client.user} has connected to Discord!')

async def send_discord_message(text: str, ds_id: int, file=None):
    channel = discord_client.get_channel(ds_id)
    if channel:
        if file:
            await channel.send(content=text, file=file)
        else:
            await channel.send(content=text)

@telegram_client.on(events.NewMessage(chats=1002478633703))
async def handle_new_message(event):
    message = event.message
    if message.text:
        await send_discord_message(message.text, 1318328444227944579)
    if message.photo:
        image = io.BytesIO()
        await telegram_client.download_media(message.photo, file=image)
        image.seek(0)
        discord_file = File(image, filename="image.jpg")
        caption = message.text if message.text else "Image from Telegram"
        await send_discord_message(caption, 1318328444227944579, file=discord_file)

@telegram_client.on(events.NewMessage(chats=1002209371269))
async def handle_new_message(event):
    message = event.message
    if message.text:
        await send_discord_message(message.text, 1318332562652926025)
    if message.photo:
        image = io.BytesIO()
        await telegram_client.download_media(message.photo, file=image)
        image.seek(0)
        discord_file = File(image, filename="image.jpg")
        caption = message.text if message.text else "Image from Telegram"
        await send_discord_message(caption, 1318332562652926025, file=discord_file)

async def main():
    await telegram_client.start()
    print("Telegram client started")
    await discord_client.start(DISCORD_TOKEN)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
        loop.run_forever()  # Keep the bot running
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(telegram_client.disconnect())
        loop.run_until_complete(discord_client.close())
        loop.close()
