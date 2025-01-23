import asyncio
import os
import re
from telethon import TelegramClient, events
from telethon.tl.types import KeyboardButtonCallback
import time
import keyboard
from blessed import Terminal
import random
from collections import namedtuple
from dotenv import load_dotenv
import win32gui
import win32process
import psutil
load_dotenv()

API_ID = int(os.environ.get('API_ID'))
API_HASH = os.environ.get('API_HASH')
TARGET_CHANNEL_ID = int(os.environ.get('TARGET_CHANNEL_ID', 1002209371269))
BOT_CHANNEL_ID = os.environ.get('BOT_CHANNEL_ID', 'paris_trojanbot')
BUY_MODE = os.environ.get('BUY_MODE', 'Calls')
BUY_AMOUNT = float(os.environ.get('BUY_AMOUNT', '0.02'))
NET_PNL = float(os.environ.get('NET_PNL', '0'))
refresh = False
log_messages = []
busy=False

BalanceInfo = namedtuple('BalanceInfo', ['sol', 'usd'])
balance_info = BalanceInfo(0.0, 0.0)
last_balance_check = 0
positions_value = 0.0
daily = -1
Coins = []

term = Terminal()

balance_pattern = r'Balance: \*\*([\d.]+) SOL \(\$([\d.]+)\)\*\*'

pattern = r'\[?\*\*(?P<coin_name>[A-Z]+)\*\*\]?.*?- \*\*[\d.]+ SOL \(\$(?P<price>[\d.]+)\)\*\*.*?Price & MC: \*\*\$[\d.]+\*\* — \*\*\$(?P<market_cap>[\d.]+K?)\*\*.*?Avg Entry: \$[\d.]+ — \$(?P<avg_entry>[\d.]+K?).*?Buys: `[\d.]+ SOL \(\$(?P<buy_amount>[\d.]+)\).*?PNL USD: `(?P<pnl_percent>-?[\d.]+)%` \(`(?P<pnl_usd>-?\$[\d.]+)`\)'

test = "**Manage your tokens** 1/1[⠀](https://dexscreener.com/solana/2ss8NR7PM21r254hQXAZRmoLuqk6x89c75YmQWfLpump?id=492d0a17&ref=trojan) — W2 Wallet: `EL8wNReEPncBTf3vniHmnn3Hd9T6Lmb3Fh3T1tsr62Cp` — [W2 ✏️](https://t.me/paris_trojanbot?start=walletMenu) Balance: **0.011 SOL ($2.84)** Positions: **0.004 SOL ($1.17)** [**MILADY**](https://t.me/paris_trojanbot?start=sellToken-2ss8NR7PM21r254hQXAZRmoLuqk6x89c75YmQWfLpump) - [📈](https://dexscreener.com/solana/2ss8NR7PM21r254hQXAZRmoLuqk6x89c75YmQWfLpump?maker=EL8wNReEPncBTf3vniHmnn3Hd9T6Lmb3Fh3T1tsr62Cp&ref=trojan) - **0.0037 SOL ($0.96)** [[Hide]](https://t.me/paris_trojanbot?start=hideToken-2ss8NR7PM21r254hQXAZRmoLuqk6x89c75YmQWfLpump) `2ss8NR7PM21r254hQXAZRmoLuqk6x89c75YmQWfLpump` • Price & MC: **$0.000023** — **$23K** • Avg Entry: $0.00006195 — $61.95K • Balance: `41.59K` (0.004%) • Buys: `0.0102 SOL ($2.58) • (1 buys)` • Sells: `N/A • (0 sells)` • PNL USD: `-62.88%` (`-$1.62`) 🟥 • PNL SOL: `-62.86%` (`-0.0065 SOL`) 🟥 [PNL Card 🖼️](https://t.me/paris_trojanbot?start=genPnlC-2ss8NR7PM21r254hQXAZRmoLuqk6x89c75YmQWfLpump) [**TEST**](https://t.me/paris_trojanbot?start=sellToken-Gi7xnNqtoFubCxd8m9rUge53fftwC4hJW1waBwUjwbvE) - [📈](https://dexscreener.com/solana/Gi7xnNqtoFubCxd8m9rUge53fftwC4hJW1waBwUjwbvE?maker=EL8wNReEPncBTf3vniHmnn3Hd9T6Lmb3Fh3T1tsr62Cp&ref=trojan) - **0.0008 SOL ($0.21)** [[Hide]](https://t.me/paris_trojanbot?start=hideToken-Gi7xnNqtoFubCxd8m9rUge53fftwC4hJW1waBwUjwbvE) `Gi7xnNqtoFubCxd8m9rUge53fftwC4hJW1waBwUjwbvE` • Price & MC: **$0.00003393** — **$33.9K** • Avg Entry: $0.00009103 — $90.98K • Balance: `6.31K` • Buys: `0.003 SOL ($0.57) • (1 buys)` • Sells: `N/A • (0 sells)` • PNL USD: `-62.73%` (`-$0.36`) 🟥 • PNL SOL: `-72.00%` (`-0.0022 SOL`) 🟥 [PNL Card 🖼️](https://t.me/paris_trojanbot?start=genPnlC-Gi7xnNqtoFubCxd8m9rUge53fftwC4hJW1waBwUjwbvE)__"

async def update_balance(client):
    global balance_info, last_balance_check, refresh, Coins, positions_value, daily, busy
    while True:
        if busy == False:
            if refresh and time.time() - last_balance_check > 0.1:
                async for message in client.iter_messages(BOT_CHANNEL_ID, limit=1):
                    if "You do not have any tokens yet" in message.text:
                        log("Don't turn on refresh mode when you don't have any tokens...")
                        refresh = False
                        log("Disabled refresh mode")
                    else:
                        if "Manage your tokens" not in message.text and busy == False:
                            await client.send_message(BOT_CHANNEL_ID, "/positions")
                            await asyncio.sleep(2)  # Wait for the response
                        else:
                            await click_button_with_text(client, BOT_CHANNEL_ID, "Refresh")
                        
                        async for new_message in client.iter_messages(BOT_CHANNEL_ID, limit=1):
                            match = re.search(balance_pattern, new_message.text)
                            if match:
                                balance_info = BalanceInfo(float(match.group(1)), float(match.group(2)))

                            matches = re.finditer(pattern, message.text)
                            if matches:
                                Coins = list(matches)

                            positions_pattern = r'Positions: \*\*([\d.]+) SOL \(\$[\d.]+\)\*\*'
                            match = re.search(positions_pattern, message.text)
                            if match:
                                positions_value = float(match.group(1))

                            if daily == -1:
                                daily = round(positions_value + balance_info.usd,2)

                
                last_balance_check = time.time()
        await asyncio.sleep(1)

address_pattern = r'\b[A-Za-z0-9]{32,44}(?:pump)?\b|\bhttps?://pump\.fun/coin/[A-Za-z0-9]{32,44}pump\b|\bhttps?://dexscreener\.com/solana/([A-Za-z0-9]{32,44})\b|\(([A-Za-z0-9]{32,44})\)'

def change_buy_mode():
    global BUY_MODE
    modes = ['ALL', 'NoPump', 'Calls', 'None']
    current_index = modes.index(BUY_MODE)
    BUY_MODE = modes[(current_index + 1) % len(modes)]
    log(f"Buy mode changed to: {BUY_MODE}")

def change_buy_amount(amount):
    global BUY_AMOUNT
    BUY_AMOUNT = round(BUY_AMOUNT + amount, 2)
    log(f"Buy amount changed to: {BUY_AMOUNT}")

def log(message):
    log_messages.append(message)
    if len(log_messages) > 10:
        log_messages.pop(0)

def generate_display(client):
    global Coins, daily, NET_PNL
    lines = []
    lines.append(term.cyan + term.bold("bobTMM - Server V0.5.0"))
    lines.append(term.yellow(f"R - refresh, B - change buy mode ({BUY_MODE}), -/+ change buy amount by 0.01 ({BUY_AMOUNT})"))
    lines.append(term.green("- " * 40))
    
    if refresh:
        lines.append(term.white + f"SOL: {balance_info.sol} SOL (${balance_info.usd})")
        color = term.green if round((positions_value+balance_info.usd) - NET_PNL,2) > 0 else term.red
        lines.append(color + f"Net PNL: {round((positions_value+balance_info.usd) - NET_PNL,2)} ({round((((positions_value+balance_info.usd) - NET_PNL) / NET_PNL)*100,2)}%)")
        color = term.green if round((positions_value+balance_info.usd) - daily,2) > 0 else term.red
        lines.append(color + f"Daily PNL: {round((positions_value+balance_info.usd) - daily,2)} ({round((((positions_value+balance_info.usd) - daily) / daily)*100,2)}%)")
        for coin in Coins:
            color = term.green if float(coin.group('pnl_percent')) > 0 else term.red
            lines.append(color + f"{coin.group('coin_name')} - ${coin.group('price')} | PNL USD: {coin.group('pnl_percent')}% ({coin.group('pnl_usd')}) | MC: {coin.group('market_cap')} | Avg Entry: {coin.group('avg_entry')}")
    else:
        lines.extend([])
    
    lines.append(term.green("- " * 40))
    lines.extend([term.white(msg) for msg in log_messages])
    
    # Ensure the display always has a consistent number of lines
    while len(lines) < term.height:
        lines.append("")
    
    return lines

async def update_display(client):
    old_lines = []
    with term.fullscreen(), term.hidden_cursor():
        while True:
            new_lines = generate_display(client)
            for i, (old, new) in enumerate(zip(old_lines + [""]*len(new_lines), new_lines)):
                if old != new:
                    print(term.move(i, 0) + new + term.clear_eol)
            old_lines = new_lines
            await asyncio.sleep(0.1)

def toggle_refresh():
    global refresh
    refresh = not refresh


async def click_button_text(client, chat_id, phrase):
    try:
        async for message in client.iter_messages(chat_id, limit=1):
            if message.reply_markup:
                for row in message.reply_markup.rows:
                    for button in row.buttons:
                        if phrase.lower() == button.text.lower().strip("✅ ").strip(" ✏️"):
                            await message.click(text=button.text)
                            #log(f"Clicked button with text that is '{phrase}'")
                            return True
        #log(f"No button found with text containing '{phrase}'")
        return False
    except Exception as e:
        #log(f"Error clicking button: {e}")
        return False

async def click_button_with_text(client, chat_id, phrase):
    try:
        async for message in client.iter_messages(chat_id, limit=1):
            if message.reply_markup:
                for row in message.reply_markup.rows:
                    for button in row.buttons:
                        if phrase.lower() in button.text.lower():
                            await message.click(text=button.text)
                            #log(f"Clicked button with text containing '{phrase}'")
                            return True
        #log(f"No button found with text containing '{phrase}'")
        return False
    except Exception as e:
        #log(f"Error clicking button: {e}")
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
        log(f"Timeout waiting for message in {chat_id}")
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
    global busy
    async with TelegramClient('bob', API_ID, API_HASH) as client:
        @client.on(events.NewMessage(chats=TARGET_CHANNEL_ID))
        async def handler(event):
            global busy
            busy = True
            message = event.message.text
            match = re.search(address_pattern, message)
            if match:
                address = match.group(1) or match.group(2) or match.group(0)
                if address.startswith('http'):
                    address = address.split('/')[-1]
                params=""
                if "!buy" in message:
                    params += "!buy "
                if "!snipe" in message:
                    params += "!snipe "

                log(f"detected adress: {address} with parameters: {params}")

                if BUY_MODE == "NoPump" and "!snipe" in message:
                    log('skipping pump call as buy mode is {BUY_MODE}')
                    busy = False
                    return

                if BUY_MODE == "Calls" and "!buy" not in message:
                    log('skipping non-call as buy mode is {BUY_MODE}')
                    busy = False
                    return

                if BUY_MODE == "None":
                    log('skipping adress as buy mode is {BUY_MODE}')
                    busy = False
                    return

                await client.send_message(BOT_CHANNEL_ID, address)

                response = await wait_for_message(client, BOT_CHANNEL_ID, 30)
                if response is None or "Token not found" in response.message.text:
                    return
                
                if "!snipe" in message:
                    await click_button_with_text(client, BOT_CHANNEL_ID, "limit")
                    button_text1 = await find_button_with_text(client, BOT_CHANNEL_ID, "migration")
                    if button_text1:
                        await click_button_with_text(client, BOT_CHANNEL_ID, "migration")
                    else:
                        await click_button_with_text(client, BOT_CHANNEL_ID, "event")
                        await click_button_with_text(client, BOT_CHANNEL_ID, "migration")

                    button_text = await find_button_with_text(client, BOT_CHANNEL_ID, f"{BUY_AMOUNT} SOL")
                    if await click_button_text(client, BOT_CHANNEL_ID, f"{BUY_AMOUNT} SOL"):
                        log(button_text)
                        if button_text and "✏️" in button_text:
                            await client.send_message(BOT_CHANNEL_ID, BUY_AMOUNT)
                    else:
                        await click_button_with_text(client, BOT_CHANNEL_ID, "SOL ✏️")
                        await client.send_message(BOT_CHANNEL_ID, BUY_AMOUNT)
                    time.sleep(0.25)
                    await click_button_with_text(client, BOT_CHANNEL_ID, "CREATE ORDER")
                else:
                    await click_button_with_text(client, BOT_CHANNEL_ID, "swap")

                    button_text = await find_button_with_text(client, BOT_CHANNEL_ID, f"{BUY_AMOUNT} SOL")
                    if await click_button_text(client, BOT_CHANNEL_ID, f"{BUY_AMOUNT} SOL"):
                        log(button_text)
                        if button_text and "✏️" in button_text:
                            await client.send_message(BOT_CHANNEL_ID, BUY_AMOUNT)
                    else:
                        await click_button_with_text(client, BOT_CHANNEL_ID, "SOL ✏️")
                        await client.send_message(BOT_CHANNEL_ID, BUY_AMOUNT)
            time.sleep(0.5)
            busy = False

        log(f"Bot is running. Monitoring channel {TARGET_CHANNEL_ID}. Press Ctrl+C to stop.")

        def is_console_focused():
            foreground_window = win32gui.GetForegroundWindow()
            _, process_id = win32process.GetWindowThreadProcessId(foreground_window)
            return psutil.Process(process_id).name() == "WindowsTerminal.exe"

        def create_focused_callback(callback):
            def wrapper(*args, **kwargs):
                if is_console_focused():
                    callback(*args, **kwargs)
            return wrapper

        # Replace the existing keyboard bindings with these:
        keyboard.add_hotkey("r", create_focused_callback(toggle_refresh))
        keyboard.add_hotkey("b", create_focused_callback(change_buy_mode))
        keyboard.add_hotkey("-", create_focused_callback(lambda: change_buy_amount(-0.01)))
        keyboard.add_hotkey("+", create_focused_callback(lambda: change_buy_amount(0.01)))

        await asyncio.gather(
            update_display(client),
            update_balance(client)
        )


        await client.run_until_disconnected()

async def main():
    await bot()

if __name__ == "__main__":
    asyncio.run(main())
