import asyncio
import re
from telethon import TelegramClient, events
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import ttk
import numpy as np
from tkinter import BooleanVar
import random
import threading
import os

channel = 1002209371269
is_processing = False
last_processed_message_id = None
pnl_history = []
max_history_length = 100
debugsmg = "Balance: 0.084 SOL ($15.67) DALMATIAN (https://t.me/paris_trojanbot?start=sellToken-3CSeAGiw5TYeuZfB74adUM1M9if1fEDXzr5PrnuNpump) - 📈 (https://dexscreener.com/solana/3CSeAGiw5TYeuZfB74adUM1M9if1fEDXzr5PrnuNpump?maker=EL8wNReEPncBTf3vniHmnn3Hd9T6Lmb3Fh3T1tsr62Cp&ref=trojan) - 0.0334 SOL ($6.16) [Hide] (https://t.me/paris_trojanbot?start=hideToken-3CSeAGiw5TYeuZfB74adUM1M9if1fEDXzr5PrnuNpump) 3CSeAGiw5TYeuZfB74adUM1M9if1fEDXzr5PrnuNpump • Price & MC: $0.001655 — $1.65M • Avg Entry: $0.0009963 — $996.28K • Balance: 3.72K • Buys: 0.0201 SOL ($3.71) • (1 buys) • Sells: N/A • (0 sells) • PNL USD: +66.11% ($2.45) 🟩 • PNL SOL: +65.82% (0.0132 SOL) 🟩 PNL Card 🖼️ (https://t.me/paris_trojanbot?start=genPnlC-3CSeAGiw5TYeuZfB74adUM1M9if1fEDXzr5PrnuNpump) GAYLA (https://t.me/paris_trojanbot?start=sellToken-5binunNTSPdpkG45C6bag5bVm7hVjScJpEKgUbhBpump) - 📈 (https://dexscreener.com/solana/5binunNTSPdpkG45C6bag5bVm7hVjScJpEKgUbhBpump?maker=EL8wNReEPncBTf3vniHmnn3Hd9T6Lmb3Fh3T1tsr62Cp&ref=trojan) - 0.002 SOL ($0.38) [Hide] (https://t.me/paris_trojanbot?start=hideToken-5binunNTSPdpkG45C6bag5bVm7hVjScJpEKgUbhBpump) 5binunNTSPdpkG45C6bag5bVm7hVjScJpEKgUbhBpump • Price & MC: $0.00001121 — $11.21K • Avg Entry: $0.0001107 — $110.72K • Balance: 34.07K (0.003%) • Buys: 0.0201 SOL ($3.77) • (1 buys) • Sells: N/A • (0 sells) • PNL USD: -89.88% (-$3.39) 🟥 • PNL SOL: -89.72% (-0.0182 SOL) 🟥 PNL Card 🖼️ (https://t.me/paris_trojanbot?start=genPnlC-5binunNTSPdpkG45C6bag5bVm7hVjScJpEKgUbhBpump)"

test1 = 6.16
test2 = 0.38

COOL_GRAY = "#2F3136"
LIGHT_GRAY = "#40444B"
TEXT_COLOR = "#FFFFFF"
PNL_COLOR = "#FF5733"
POSITIVE_COLOR = "#00FF00"
NEGATIVE_COLOR = "#FF0000"

api_id = int(os.environ.get('API_ID'))
api_hash = os.environ.get('API_HASH')
channel = int(os.environ.get('CHANNEL_ID', 1002209371269))
buy_enabled = os.environ.get('BUY_ENABLED', 'False').lower() == 'true'
debug = os.environ.get('DEBUG', 'False').lower() == 'true'
starting_balance = float(os.environ.get('STARTING_BALANCE', '0'))
sol_amount = float(os.environ.get('SOL_AMOUNT', '0'))

debug_coin_values = [0.0]
last_balance = starting_balance

print(f"starting balance: {starting_balance}")
print(f"buying at: {sol_amount} SOL")
print(f"buy enabled: {buy_enabled}")

refresh_enabled = None


async def press_button(client, button_text):
    async for message in client.iter_messages('paris_trojanbot', limit=1):
        if message.reply_markup:
            for row in message.reply_markup.rows:
                for button in row.buttons:
                    if button_text in button.text:
                        await message.click(text=button.text)
                        return True
    return False


def clean_currency(x):
    if isinstance(x, str):
        return x.strip('`').replace('$', '').replace(',', '')
    return x


async def check_pnl(client):
    global current_balance2
    async for message in client.iter_messages('paris_trojanbot', limit=1):
        print("got message from bot")

        if not "Manage your tokens" in message.text:
            print("{Manage your tokens} not detected")
            balance_match = re.search(r'Balance: .+? \(\$([\d.]+)\)', message.text)
            current_balance1 = float(balance_match.group(1))
            print(f"Detected balance: ${current_balance1}")
            return [], current_balance1
        else:
            print("{Manage your tokens} is detected")
            #print(f"text: {message.text}")
            balance_match2 = re.search(r'Balance: .+? \(\$([\d.]+)\)', message.text)
            current_balance2 = float(balance_match2.group(1))
            print(current_balance2)

            coin_values = re.findall(r'\- \*\*[\d.]+ SOL \(\$(\d+\.\d+)\)\*\*', message.text)

            print(f"coins detected: {coin_values}")

            if coin_values:
                coin_values = [float(value) for value in coin_values]
                total_coin_value = sum(coin_values)
                current_balance2 = float(balance_match2.group(1)) if balance_match2 else last_balance
                total_value = current_balance2 + total_coin_value
                print(f"Detected balance: ${current_balance2}, Total value: ${total_value}")
                return coin_values, total_value

    print("No balance detected, using last balance")
    return [], last_balance


def update_gui(coin_values, total_value):
    global pnl_history, last_balance

    total_coin_value = sum(coin_values)
    current_balance = total_value - total_coin_value
    total_assets = current_balance + total_coin_value
    value_change = total_assets - starting_balance

    pnl_text.set("\n".join([f"Coin {i + 1}: ${value:.2f}" for i, value in enumerate(coin_values)]))
    net_pnl_text.set(f"Net PNL: ${value_change:.2f}")
    balance_text.set(f"Net balance: ${total_assets:.2f}")

    pnl_history.append(total_assets)
    pnl_history = pnl_history[-max_history_length:]

    ax.clear()
    x = np.arange(len(pnl_history))
    color = POSITIVE_COLOR if total_assets >= starting_balance else NEGATIVE_COLOR
    ax.fill_between(x, starting_balance, pnl_history, color=color, alpha=0.3)
    ax.plot(x, pnl_history, color=PNL_COLOR, linewidth=3)
    ax.axhline(y=starting_balance, color='white', linestyle='--', alpha=0.5)

    if len(pnl_history) > 1:
        y_min, y_max = min(min(pnl_history), starting_balance), max(max(pnl_history), starting_balance)
        y_range = y_max - y_min
        ax.set_ylim([y_min - 0.1 * y_range, y_max + 0.1 * y_range])

    ax.set_facecolor(COOL_GRAY)
    ax.set_xlabel('Time', color=TEXT_COLOR)
    ax.set_ylabel('Balance (USD)', color=TEXT_COLOR)
    ax.set_title('Total Assets Over Time', color=TEXT_COLOR)
    ax.set_xticks([])
    ax.grid(True, linestyle='--', alpha=0.7, color=LIGHT_GRAY)
    ax.tick_params(axis='y', colors=TEXT_COLOR)

    for spine in ax.spines.values():
        spine.set_edgecolor(TEXT_COLOR)
        spine.set_linewidth(0.5)

    canvas.draw()
    root.configure(bg="#3d3d3d")

    last_balance = current_balance


async def periodic_pnl_check(client):
    last_refresh_state = True
    start_command_sent = False

    while True:
        current_refresh_state = refresh_enabled.get()

        if current_refresh_state != last_refresh_state:
            if not current_refresh_state:
                # Refresh was just turned off
                if not start_command_sent:
                    await client.send_message('paris_trojanbot', '/start')
                    await asyncio.sleep(2)  # Wait a bit longer for the response
                    _, current_balance = await check_pnl(client)
                    root.after(0, update_gui, [], current_balance)
                    start_command_sent = True
            else:
                # Refresh was just turned on
                start_command_sent = False

        if current_refresh_state and not is_processing:
            async for message in client.iter_messages('paris_trojanbot', limit=1):
                if "Manage your tokens" in message.text:
                    await press_button(client, "Refresh")
                    await asyncio.sleep(1)
                    pnls, current_balance = await check_pnl(client)
                    root.after(0, update_gui, pnls, current_balance)
                else:
                    await client.send_message('paris_trojanbot', '/positions')
                    await asyncio.sleep(1)
                    pnls, current_balance = await check_pnl(client)
                    root.after(0, update_gui, pnls, current_balance)

        last_refresh_state = current_refresh_state
        await asyncio.sleep(1)

async def handle_new_message(event, client):
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

    match = re.search(r'\$\s+(\S+)', message)
    limit_match = re.search(r'@!\s*(\S+)', message)

    if match:
        extracted_url = match.group(1)
        await client.send_message('paris_trojanbot', extracted_url)

        await asyncio.sleep(1)  # Wait for new message

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

                # Look for the button with the specified SOL amount
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

            # Look for the button with the specified SOL amount
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
        client.add_event_handler(lambda e: asyncio.create_task(handle_new_message(e, client)),
                                 events.NewMessage(chats=channel, pattern=r'\$\s+(\S+)'))
        await periodic_pnl_check(client)


async def main():
    global refresh_enabled
    global root, pnl_text, net_pnl_text, balance_text, ax, canvas

    root = tk.Tk()
    root.title("PNL Tracker")
    root.configure(bg=COOL_GRAY)

    style = ttk.Style()
    style.theme_use('clam')
    style.configure('TLabel', background=COOL_GRAY, foreground=TEXT_COLOR)

    pnl_text = tk.StringVar()
    net_pnl_text = tk.StringVar()
    balance_text = tk.StringVar()

    ttk.Label(root, textvariable=pnl_text).pack(pady=5)
    ttk.Label(root, textvariable=net_pnl_text).pack(pady=5)
    ttk.Label(root, textvariable=balance_text).pack(pady=5)

    refresh_enabled = BooleanVar(value=False)
    refresh_checkbox = ttk.Checkbutton(root, text="Enable Refresh", variable=refresh_enabled)
    refresh_checkbox.pack(pady=10)

    fig, ax = plt.subplots(figsize=(10, 6), facecolor=COOL_GRAY)
    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    client_task = asyncio.create_task(run_client())

    while True:
        root.update()
        await asyncio.sleep(0.1)



if __name__ == "__main__":
    asyncio.run(main())
