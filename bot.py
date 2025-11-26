# pure_scalper_fixed.py  ← ဒါကို သုံးပါ!
import ccxt.async_support as ccxt
import asyncio
import time
from datetime import datetime

SYMBOLS = ['BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT', 'AVAX/USDT:USDT', '1000PEPE/USDT:USDT']
LEVERAGE = 20
POSITION_USD = 35
TP_PCT = 0.0052      # +0.52% gross
SL_PCT = 0.0029      # -0.29%
MAX_POSITIONS = 10

balance = 500.0
initial_balance = balance
positions = {}
cooldown = {}

exchange = ccxt.binance({
    'enableRateLimit': True,
    'options': {'defaultType': 'future'}
})

async def fetch_ohlcv(symbol, timeframe='15s', limit=100):
    try:
        return await exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    except:
        return None

def ema(values, period):
    k = 2 / (period + 1)
    ema_val = values[0]
    for price in values[1:]:
        ema_val = price * k + ema_val * (1 - k)
    return ema_val

def calculate_rsi(prices, period=14):
    if len(prices) < period + 1:
        return 50
    gains = 0
    losses = 0
    for i in range(1, period + 1):
        diff = prices[-i] - prices[-i-1]
        if diff > 0:
            gains += diff
        else:
            losses -= diff
    if losses == 0:
        return 100
    rs = gains / losses
    return 100 - (100 / (1 + rs))

async def scalper():
    global balance
    while True:
        try:
            for symbol in SYMBOLS:
                if symbol in cooldown and time.time() < cooldown[symbol]:
                    continue
                if len(positions) >= MAX_POSITIONS:
                    continue

                data_15s = await fetch_ohlcv(symbol, '15s', 100)
                data_1m  = await fetch_ohlcv(symbol, '1m', 50)
                if not data_15s or len(data_15s) < 50 or not data_1m:
                    continue

                price = data_15s[-1][4]
                close_15s = [x[4] for x in data_15s]
                close_1m  = [x[4] for x in data_1m]

                ema8_15s  = ema(close_15s[-21:], 8)
                ema21_15s = ema(close_15s[-40:], 21)
                ema8_1m   = ema(close_1m[-21:], 8)
                ema21_1m  = ema(close_1m[-40:], 21)

                rsi = calculate_rsi(close_15s, 14)

                # LONG
                if (ema8_15s > ema21_15s and
                    ema8_1m > ema21_1m and          # 1m မှာလည်း bullish
                    rsi < 42 and
                    price < ema8_15s * 1.003):      # pullback ထဲမှာ

                    qty = (POSITION_USD * LEVERAGE) / price
                    positions[symbol] = {
                        'side': 'LONG', 'entry': price, 'qty': qty,
                        'tp': price * (1 + TP_PCT), 'sl': price * (1 - SL_PCT)
                    }
                    cooldown[symbol] = time.time() + 4
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] LONG  {symbol.split(':')[0]} @ {price:.4f}")

                # SHORT
                elif (ema8_15s < ema21_15s and
                      ema8_1m < ema21_1m and
                      rsi > 58 and
                      price > ema8_15s * 0.997):

                    qty = (POSITION_USD * LEVERAGE) / price
                    positions[symbol] = {
                        'side': 'SHORT', 'entry': price, 'qty': qty,
                        'tp': price * (1 - TP_PCT), 'sl': price * (1 + SL_PCT)
                    }
                    cooldown[symbol] = time.time() + 4
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] SHORT {symbol.split(':')[0]} @ {price:.4f}")

            # Check exits
            to_remove = []
            for symbol, pos in list(positions.items()):
                current = (await fetch_ohlcv(symbol, '15s', 1))[0][4]
                pnl_pct = (current - pos['entry']) / pos['entry'] * (1 if pos['side']=='LONG' else -1)

                if (pos['side']=='LONG' and (current >= pos['tp'] or current <= pos['sl'])) or \
                   (pos['side']=='SHORT' and (current <= pos['tp'] or current >= pos['sl'])):
                    profit = POSITION_USD * LEVERAGE * pnl_pct * 0.998
                    balance += profit
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] {'WIN' if profit>0 else 'LOSS'} {symbol.split(':')[0]} | +${profit:.2f} → ${balance:.1f}")
                    to_remove.append(symbol)

            for s in to_remove:
                del positions[s]

            if int(time.time()) % 20 == 0:
                daily = (balance / initial_balance - 1) * 100
                print(f"BALANCE: ${balance:.1f} | Today: {daily:+.2f}% | Open: {len(positions)}")

            await asyncio.sleep(1.1)

        except Exception as e:
            print("Error:", e)
            await asyncio.sleep(5)

print("Pure Scalper FIXED v1.1 - အခု တကယ် ဝင်တော့မယ်!")
asyncio.run(scalper())
