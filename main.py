import asyncio
import re
from telethon import TelegramClient, events
import matplotlib.pyplot as plt
import numpy as np
import os
from dotenv import load_dotenv
from flask import Flask, render_template, jsonify

app = Flask(__name__)

load_dotenv()

# Configuration
channel = 1002209371269
is_processing = False
last_processed_message_id = None
pnl_history = []
max_history_length = 100

# Environment variables
api_id = int(os.getenv('API_ID'))
api_hash = os.getenv('API_HASH')
buy_enabled = os.getenv('BUY_ENABLED', 'False').lower() == 'true'
debug = os.getenv('DEBUG', 'False').lower() == 'true'
starting_balance = float(os.getenv('STARTING_BALANCE', '0'))
sol_amount = float(os.getenv('SOL_AMOUNT', '0'))

print(f"starting balance: {starting_balance}")
print(f"buying at: {sol_amount} SOL")
print(f"buy enabled: {buy_enabled}")

last_balance = starting_balance
current_balance = starting_balance

async def check_pnl(client):
    global current_balance
    async for message in client.iter_messages('paris_trojanbot', limit=1):
        if "Manage your tokens" not in message.text:
            balance_match = re.search(r'Balance: .+? \(\$([\d.]+)\)', message.text)
            current_balance = float(balance_match.group(1)) if balance_match else last_balance
            return [], current_balance
        else:
            balance_match = re.search(r'Balance: .+? \(\$([\d.]+)\)', message.text)
            current_balance = float(balance_match.group(1)) if balance_match else last_balance
            coin_values = re.findall(r'\- \*\*[\d.]+ SOL \(\$(\d+\.\d+)\)\*\*', message.text)
            if coin_values:
                coin_values = [float(value) for value in coin_values]
                total_coin_value = sum(coin_values)
                total_value = current_balance + total_coin_value
                return coin_values, total_value
    return [], current_balance

async def periodic_pnl_check(client):
    global pnl_history
    while True:
        pnls, total_value = await check_pnl(client)
        pnl_history.append(total_value)
        pnl_history = pnl_history[-max_history_length:]
        await asyncio.sleep(60)  # Check every minute

async def handle_new_message(event, client):
    global is_processing, last_processed_message_id
    if event.message.id == last_processed_message_id or is_processing:
        return
    is_processing = True
    message = event.message.text
    match = re.search(r'\$\s+(\S+)', message)
    if match:
        extracted_url = match.group(1)
        await client.send_message('paris_trojanbot', extracted_url)
        await asyncio.sleep(1)
        if buy_enabled:
            await press_button(client, f"{sol_amount} SOL")
        print(f"Attempted to buy {sol_amount} SOL of {extracted_url}")
    last_processed_message_id = event.message.id
    is_processing = False

async def press_button(client, button_text):
    async for message in client.iter_messages('paris_trojanbot', limit=1):
        if message.reply_markup:
            for row in message.reply_markup.rows:
                for button in row.buttons:
                    if button_text in button.text:
                        await message.click(text=button.text)
                        return True
    return False

async def run_client():
    client = TelegramClient('bob', api_id, api_hash)
    async with client:
        print("Bot successfully started and listening for messages.")
        client.add_event_handler(lambda e: asyncio.create_task(handle_new_message(e, client)), events.NewMessage(chats=channel, pattern=r'\$\s+(\S+)'))
        await periodic_pnl_check(client)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/update_pnl')
def update_pnl():
    global pnl_history, starting_balance
    labels = list(range(len(pnl_history)))
    data = {
        'labels': labels,
        'data': pnl_history,
        'startingBalance': starting_balance
    }
    return jsonify(data)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(run_client())
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
