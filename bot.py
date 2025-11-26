# sol_avax_scalper.py  ← အခု ချက်ချင်း run ပါ!
import ccxt.async_support as ccxt
import asyncio
import time
from datetime import datetime

exchange = ccxt.binance({
    'enableRateLimit': True,
    'options': {'defaultType': 'future', 'adjustForTimeDifference': True},
    'timeout': 10000,
})

# အခု လိုချင်တာ SOL နဲ့ AVAX ပဲ
SYMBOLS = ['SOL/USDT:USDT', 'AVAX/USDT:USDT']

balance = 500.0
initial_balance = balance
positions = {}
last_trade = {}

async def get_price(sym):
    ticker = await exchange.fetch_ticker(sym)
    return ticker['last']

async def bot():
    global balance
    print("SOL + AVAX ONLY SCALPER STARTED - နှစ်ဖက်စလုံး စားမယ်!")

    while True:
        try:
            for sym in SYMBOLS:
                if sym in positions or len(positions) >= 6:
                    continue
                if sym in last_trade and time.time() - last_trade[sym] < 8:
                    continue

                price = await get_price(sym)
                coin = sym.split('/')[0]

                # === AVAX ===
                if coin == "AVAX":
                    if price <= 12.05:                                      # အရမ်းချိုး → LONG
                        positions[sym] = {'side': 'LONG', 'entry': price, 'time': time.time()}
                        last_trade[sym] = time.time()
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] LONG  AVAX @ {price:.4f}")

                    elif price >= 12.72:                                    # အရမ်းတက် → SHORT
                        positions[sym] = {'side': 'SHORT', 'entry': price, 'time': time.time()}
                        last_trade[sym] = time.time()
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] SHORT AVAX @ {price:.4f}")

                # === SOL ===
                if coin == "SOL":
                    if price <= 162.0:                                      # oversold → LONG
                        positions[sym] = {'side': 'LONG', 'entry': price, 'time': time.time()}
                        last_trade[sym] = time.time()
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] LONG  SOL @ {price:.2f}")

                    elif price >= 178.5:                                    # overbought → SHORT
                        positions[sym] = {'side': 'SHORT', 'entry': price, 'time': time.time()}
                        last_trade[sym] = time.time()
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] SHORT SOL @ {price:.2f}")

            # === Exit ===
            remove = []
            for sym, pos in positions.items():
                price = await get_price(sym)
                pnl_pct = (price - pos['entry']) / pos['entry'] * (1 if pos['side']=='LONG' else -1) * 100
                held = time.time() - pos['time']

                if pnl_pct >= 0.78 or pnl_pct <= -0.33 or held > 48:   # TP +0.78%  SL -0.33%  max 48s
                    profit = 35 * 20 * (pnl_pct / 100) * 0.998          # $35 × 20x
                    balance += profit
                    status = "WIN" if profit > 0 else "LOSS"
                    coin = sym.split('/')[0]
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] {status} {coin} +${profit:+.2f} → Balance ${balance:.1f}")
                    remove.append(sym)

            for s in remove:
                del positions[s]

            if int(time.time()) % 20 == 0:
                daily = (balance / initial_balance - 1) * 100
                print(f"BALANCE ${balance:.1f} | Today +{daily:+.2f}% | Open {len(positions)}")

            await asyncio.sleep(1.2)

        except Exception as e:
            print("Error:", e)
            await asyncio.sleep(4)

asyncio.run(bot())
