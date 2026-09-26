"""Backtest an EMA crossover on the live window's 1-minute candles.

Each crossover, judged at a bar's close, is scored on the NEXT bar: up if it
closes higher, down if lower, a tie if unchanged. The hit rate is printed
beside the break-even a fixed payout needs. Nothing here says the rule wins;
the numbers do.

Works on the free tier (one call, up to 5,000 bars of the live window). The
free tier reads no payouts, so pass the payout you are offered.

    pip install otcharts
    export OTCHARTS_API_KEY=otc_live_...
    python backtest_ema_cross.py otc EURUSD_otc --payout 92
"""
import argparse

from otcharts import Client

p = argparse.ArgumentParser()
p.add_argument("venue", nargs="?", default="otc")
p.add_argument("symbol", nargs="?", default="EURUSD_otc")
p.add_argument("--fast", type=int, default=9)
p.add_argument("--slow", type=int, default=21)
p.add_argument("--payout", type=float, default=None, help="percent a win pays, e.g. 92")
a = p.parse_args()

otc = Client()
bars = otc.candles(a.venue, a.symbol, tf=60, limit=5000)   # ONE request
closes = [b.close for b in bars]


def ema(values, n):
    k, out = 2 / (n + 1), []
    for v in values:
        out.append(v if not out else out[-1] + k * (v - out[-1]))
    return out


fast, slow = ema(closes, a.fast), ema(closes, a.slow)
wins = losses = ties = 0
for i in range(a.slow, len(closes) - 1):
    up = fast[i - 1] <= slow[i - 1] and fast[i] > slow[i]
    down = fast[i - 1] >= slow[i - 1] and fast[i] < slow[i]
    if not (up or down):
        continue
    move = closes[i + 1] - closes[i]
    if move == 0:
        ties += 1
    elif (move > 0) == up:
        wins += 1
    else:
        losses += 1

n = wins + losses
print(f"{a.symbol} on {a.venue}: {len(bars)} bars, {n + ties} calls "
      f"({wins} won, {losses} lost, {ties} tied)")
if n:
    print(f"hit rate {100 * wins / n:.1f}% of decided calls")
if a.payout:
    print(f"break-even at a {a.payout:g}% payout: {100 * 100 / (100 + a.payout):.1f}%")
if n and n < 400:
    print("fewer than 400 decided calls: too few to tell a rate from chance")
