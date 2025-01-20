import asyncio
import os
import re
from telethon import TelegramClient, events
from telethon.tl.types import KeyboardButtonCallback

API_ID = int(os.environ.get('API_ID'))
API_HASH = os.environ.get('API_HASH')
TARGET_CHANNEL_ID = int(os.environ.get('TARGET_CHANNEL_ID', 1002209371269))
BOT_CHANNEL_ID = os.environ.get('BOT_CHANNEL_ID', 'paris_trojanbot')
BUY_MODE = os.environ.get('BUY_MODE', 'None')
BUY_AMOUNT = os.environ.get('BUY_AMOUNT', '0.1')

address_pattern = r'\b[A-Za-z0-9]{32,44}(?:pump)?\b|\bhttps?://pump\.fun/coin/[A-Za-z0-9]{32,44}pump\b|\bhttps?://dexscreener\.com/solana/([A-Za-z0-9]{32,44})\b|\(([A-Za-z0-9]{32,44})\)'

async def click_button_text(client, chat_id, phrase):
    try:
        async for message in client.iter_messages(chat_id, limit=1):
            if message.reply_markup:
                for row in message.reply_markup.rows:
                    for button in row.buttons:
                        if phrase.lower() == button.text.lower().strip("✅ ").strip(" ✏️"):
                            await message.click(text=button.text)
                            print(f"Clicked button with text that is '{phrase}'")
                            return True
        print(f"No button found with text containing '{phrase}'")
        return False
    except Exception as e:
        print(f"Error clicking button: {e}")
        return False

async def click_button_with_text(client, chat_id, phrase):
    try:
        async for message in client.iter_messages(chat_id, limit=1):
            if message.reply_markup:
                for row in message.reply_markup.rows:
                    for button in row.buttons:
                        if phrase.lower() in button.text.lower():
                            await message.click(text=button.text)
                            print(f"Clicked button with text containing '{phrase}'")
                            return True
        print(f"No button found with text containing '{phrase}'")
        return False
    except Exception as e:
        print(f"Error clicking button: {e}")
        return False

async def wait_for_message(client, chat_id, timeout):
    try:
        event_future = client.loop.create_future()

        @client.on(events.NewMessage(chats=chat_id))
        async def handler(event):
            event_future.set_result(event)
            client.remove_event_handler(handler)

        return await asyncio.wait_for(event_future, timeout=timeout)
    except asyncio.TimeoutError:
        print(f"Timeout waiting for message in {chat_id}")
        return None

async def find_button_with_text(client, chat_id, phrase):
    async for message in client.iter_messages(chat_id, limit=1):
        if message.reply_markup:
            for row in message.reply_markup.rows:
                for button in row.buttons:
                    if phrase.lower() == button.text.lower().strip("✅ ").strip(" ✏️"):
                        return button.text
    return None

async def bot():

    async with TelegramClient('bob', API_ID, API_HASH) as client:
        @client.on(events.NewMessage(chats=TARGET_CHANNEL_ID))
        async def handler(event):
            message = event.message.text
            match = re.search(address_pattern, message)
            if match:
                address = match.group(1) or match.group(2) or match.group(0)
                if address.startswith('http'):
                    address = address.split('/')[-1]

                if BUY_MODE == "Calls" and "!buy" not in message:
                    return

                if BUY_MODE == "None":
                    return

                await client.send_message(BOT_CHANNEL_ID, address)

                response = await wait_for_message(client, BOT_CHANNEL_ID, 30)
                if response is None or "Token not found" in response.message.text:
                    return

                await click_button_with_text(client, BOT_CHANNEL_ID, "swap")

                button_text = await find_button_with_text(client, BOT_CHANNEL_ID, f"{BUY_AMOUNT} SOL")
                if await click_button_text(client, BOT_CHANNEL_ID, f"{BUY_AMOUNT} SOL"):
                    print(button_text)
                    if button_text and "✏️" in button_text:
                        await client.send_message(BOT_CHANNEL_ID, BUY_AMOUNT)
                else:
                    await click_button_with_text(client, BOT_CHANNEL_ID, "SOL ✏️")
                    await client.send_message(BOT_CHANNEL_ID, BUY_AMOUNT)

        print(f"Bot is running. Monitoring channel {TARGET_CHANNEL_ID}. Press Ctrl+C to stop.")
        await client.run_until_disconnected()

async def main():
    await bot()

if __name__ == "__main__":
    asyncio.run(main())
