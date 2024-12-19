from time import sleep
from telethon.sync import TelegramClient, events
import re
import asyncio

api_id = 25713302
api_hash = "c91b3d99304a83e58e92ab9d8a8b4d82"
buy = True
buyat = "-5%"
channel = 2209371269

is_processing = False
last_processed_message_id = None

async def press_button(button_text):
    async for message in client.iter_messages('paris_trojanbot', limit=1):
        if message.reply_markup:
            for row in message.reply_markup.rows:
                for button in row.buttons:
                    if button.text == button_text:
                        await message.click(text=button_text)
                        return True
    return False

async def wait_for_new_message():
    new_message_event = asyncio.Event()

    @client.on(events.NewMessage(chats='paris_trojanbot'))
    async def new_message_handler(event):
        new_message_event.set()

    await new_message_event.wait()
    new_message_event.clear()

async def wait_for_edited_message():
    edited_message_event = asyncio.Event()

    @client.on(events.MessageEdited(chats='paris_trojanbot'))
    async def edited_message_handler(event):
        edited_message_event.set()

    await edited_message_event.wait()
    edited_message_event.clear()

with TelegramClient('bob', api_id, api_hash) as client:
    @client.on(events.NewMessage(chats=channel, pattern=r'.*\$\s+https?://\S+.*'))
    async def handler(event):
        global is_processing
        global last_processed_message_id

        if event.message.id == last_processed_message_id:
            print("This message has already been processed. Waiting for a new command.")
            return

        if is_processing:
            print("Currently processing a request. Please wait.")
            return

        is_processing = True

        message = event.message.text
        chat = await event.get_chat()
        channel_info = f"Channel ID: {chat.id}"

        match = re.search(r'\$\s+(https?://\S+)', message)
        if match:
            print(f"Message ID: {event.message.id}")
            print(channel_info)

            extracted_url = match.group(1)
            print(f"Extracted URL: {extracted_url}")

            await client.send_message('paris_trojanbot', extracted_url)

            await wait_for_new_message()

            button_pressed = await press_button('Limit')
            if button_pressed:
                print("Selected limit order")
            else:
                print("Limit button not found.")

            sleep(0.5)

            button_pressed = await press_button('Trigger Price: $-')
            if button_pressed:
                print("Selected trigger price order")

                sleep(1)

                await client.send_message('paris_trojanbot', buyat)

                sleep(5)

                if (buy == True):
                    button_pressed = await press_button('CREATE ORDER')
                    if button_pressed:
                        print(f"Created order")
                    else:
                        print("CREATE ORDER button not found.")

            else:
                print("Trigger Price button not found.")

                if (buy == True):
                    button_pressed = await press_button('CREATE ORDER')
                    if button_pressed:
                        print(f"Created order")
                    else:
                        print("CREATE ORDER button not found.")

            await client.send_message('HawkMoonCryptoTnstaff', f"Bot: bought {extracted_url}")


            last_processed_message_id = event.message.id

        is_processing = False

    client.run_until_disconnected()
