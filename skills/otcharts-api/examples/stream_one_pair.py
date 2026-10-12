"""Stream one instrument and print a 1-minute bar each time one closes.

Needs a data plan (Lite or higher): the free tier has no live stream. It
costs one request for as long as it runs; polling candles every minute
instead would cost 1,440 a day.

    pip install otcharts
    export OTCHARTS_API_KEY=otc_live_...
    python stream_one_pair.py otc EURUSD_otc
"""
import sys

from otcharts import Client

venue = sys.argv[1] if len(sys.argv) > 1 else "otc"
symbol = sys.argv[2] if len(sys.argv) > 2 else "EURUSD_otc"

otc = Client()                       # reads OTCHARTS_API_KEY
bar = None                           # [minute, open, high, low, close]
first = True                         # the first bar began mid-minute: not printed

for tick in otc.stream(venue, symbol):
    minute = tick.time - tick.time % 60
    if bar and minute != bar[0]:
        # A tick from a new minute closes the previous bar. Times are the
        # book's own clock: Pocket Option's runs 2 hours ahead of UTC.
        if not first:
            print(f"{symbol} {bar[0]}  O {bar[1]}  H {bar[2]}  L {bar[3]}  C {bar[4]}", flush=True)
        first, bar = False, None
    if bar is None:
        bar = [minute, tick.price, tick.price, tick.price, tick.price]
    else:
        bar[2] = max(bar[2], tick.price)
        bar[3] = min(bar[3], tick.price)
        bar[4] = tick.price
