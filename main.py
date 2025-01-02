import asyncio
import re
import os
from telethon import TelegramClient, events

# Use environment variables
api_id = os.environ.get('API_ID')
api_hash = os.environ.get('API_HASH')
channel = os.environ.get('CHANNEL_ID')
buy_enabled = os.environ.get('BUY_ENABLED', 'False').lower() == 'true'
debug = os.environ.get('DEBUG', 'False').lower() == 'true'
starting_balance = float(os.environ.get('STARTING_BALANCE', '0'))
sol_amount = float(os.environ.get('SOL_AMOUNT', '0'))

is_processing = False
last_processed_message_id = None

print(f"starting balance: {starting_balance}")
print(f"buying at: {sol_amount} SOL")
print(f"buy enabled: {buy_enabled}")
print("V 0.2.2 (Server edition)")

async def press_button(client, button_text):
    async for message in client.iter_messages('paris_trojanbot', limit=1):
        if message.reply_markup:
            for row in message.reply_markup.rows:
                for button in row.buttons:
                    if button_text in button.text:
                        await message.click(text=button.text)
                        return True
    return False

async def check_pnl(client):
    async for message in client.iter_messages('paris_trojanbot', limit=1):
        print("got message from bot")
        if "Manage your tokens" not in message.text:
            print("{Manage your tokens} not detected")
            balance_match = re.search(r'Balance: .+? \(\$([\d.]+)\)', message.text)
            current_balance = float(balance_match.group(1)) if balance_match else 0
            print(f"Detected balance: ${current_balance}")
            return [], current_balance
        else:
            print("{Manage your tokens} is detected")
            balance_match = re.search(r'Balance: .+? \(\$([\d.]+)\)', message.text)
            current_balance = float(balance_match.group(1)) if balance_match else 0
            coin_values = re.findall(r'\- \*\*[\d.]+ SOL \(\$(\d+\.\d+)\)\*\*', message.text)
            coin_values = [float(value) for value in coin_values]
            total_coin_value = sum(coin_values)
            total_value = current_balance + total_coin_value
            print(f"Detected balance: ${current_balance}, Total value: ${total_value}")
            return coin_values, total_value

async def handle_new_message(event, client):
    await client.send_message('me', "the bot is now active!")
    global is_processing, last_processed_message_id
    if event.message.id == last_processed_message_id:
        print("This message has already been processed. Waiting for a new command.")
        return
    if is_processing:
        print("Currently processing a request. Please wait.")
        return
    is_processing = True
    message = event.message.text
    match = re.search(r'\$\s+(\S+)', message)
    limit_match = re.search(r'@!\s*(\S+)', message)
    if match:
        extracted_url = match.group(1)
        await client.send_message('paris_trojanbot', extracted_url)
        await asyncio.sleep(1)
        if limit_match:
            print(limit_match)
            limit_price = limit_match.group(1).strip()
            button_pressed = await press_button(client, 'Limit')
            if button_pressed:
                print("Selected limit order")
                await asyncio.sleep(0.5)
                button_pressed = await press_button(client, 'Trigger Price: $-')
                if button_pressed:
                    await asyncio.sleep(1)
                    await client.send_message('paris_trojanbot', limit_price)
                    await asyncio.sleep(5)
                    if buy_enabled:
                        button_pressed = await press_button(client, f"{sol_amount} SOL")
                        if button_pressed:
                            await asyncio.sleep(2)
                            button_pressed = await press_button(client, 'CREATE ORDER')
                            print(f"Created limit order for {sol_amount} SOL at {limit_price}")
                        else:
                            print(f"Button for {sol_amount} SOL not found.")
                else:
                    print("Trigger Price button not found.")
        else:
            print("no limit found")
            await asyncio.sleep(1)
            if buy_enabled:
                button_pressed = await press_button(client, f"{sol_amount} SOL")
                if button_pressed:
                    print(f"Created market order for {sol_amount} SOL")
                else:
                    print(f"Button for {sol_amount} SOL not found.")
        print(f"Attempted to buy {sol_amount} SOL of {extracted_url}")
    last_processed_message_id = event.message.id
    is_processing = False
    print("done request")

async def run_client():
    client = TelegramClient('bob', api_id, api_hash)
    async with client:
        print("Bot successfully started and listening for messages.")
        client.add_event_handler(
            lambda e: asyncio.create_task(handle_new_message(e, client)),
            events.NewMessage(chats=channel, pattern=r'\$\s+(\S+)')
        )
        while True:
            await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(run_client())
