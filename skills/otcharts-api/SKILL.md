---
name: otcharts-api
description: Read OTC market data for Pocket Option, Quotex, IQ Option and BinoDex, plus the real FX market, from the OTCharts API (otcharts.com). It covers candles, live ticks over one stream, instrument lists and payouts, in Python (pip install otcharts) or plain HTTP. Use it when writing code that reads binary-options OTC prices, backtests on OTC candles, streams live OTC ticks, or builds a scanner or signal bot on these brokers.
---

# OTCharts market data API

OTCharts serves the price feeds of four binary-options brokers' OTC books and the
real FX market as JSON: historical candles, live ticks, instrument lists and payouts.

**Know these before you write code:**
- **It reads prices. It never places trades.** There are no orders, positions or balances.
- **No broker login is needed.** The user's key talks to OTCharts; OTCharts holds the broker connections.
- **OTC prices are made by each broker**, around the clock, including weekends. They are not the interbank market, and the same pair differs from broker to broker. Only the `forex` book is the real market.
- **Do not claim or imply that any strategy wins.** Report what the data shows and nothing more.

## Setup

1. The user makes a free key at https://otcharts.com/account. No card is needed.
2. Keep it in an environment variable: `export OTCHARTS_API_KEY=otc_live_...`. Never hard-code it.
3. For Python, run `pip install otcharts` (no dependencies; `pip install 'otcharts[pandas]'` adds `.dataframe()`).
   For any other language, send HTTP to `https://otcharts.com/v1/...` with the header
   `Authorization: Bearer $OTCHARTS_API_KEY`.

## Books (venues) and symbols

| venue id | what it is | example symbol |
|---|---|---|
| `otc` | Pocket Option | `EURUSD_otc` (equities carry `#`: `#AAPL_otc`) |
| `quotex` | Quotex | `EURUSD_otc` |
| `iq` | IQ Option | `EURUSD-OTC` |
| `binodex` | BinoDex | `EUR/USD-OTC` |
| `forex` | the real FX market | `EURUSD` |

- **Never guess a symbol.** Ids are not portable between books. List them first with
  `otc.symbols(venue)` or `GET /v1/symbols?venue=otc`.
- **Timeframes differ per book.** Read them from `GET /v1/venues`. `tf` is in seconds.
- **Clocks:** Pocket Option candle times are on the broker's clock, which runs 2 hours ahead
  of UTC. The other books are UTC.

## Pick the right call (the one decision that matters)

- **Live prices: use `stream()` / `GET /v1/stream`** (server-sent events). One request opens
  it, however long it stays open. Every tick names its own symbol. On Pocket Option (`otc`)
  and Quotex (`quotex`) one stream carries a list of symbols; IQ, BinoDex and `forex` take one
  symbol per stream. Live streams come with the data plans (Lite and up); the free tier has none.
- **History: call `candles()` / `GET /v1/candles` once** for the bars you need.
- **Never call candles on a timer.** Five instruments asked for once a minute is 7,200
  requests a day. This is how almost every account runs out of its allowance. Stream instead,
  and build bars from ticks if needed.
- **`usage()` / `GET /v1/usage` is free.** A loop may call it to check what is left and when it resets.

## Python

```python
from otcharts import Client, PlanError, QuotaExceeded, NotFound

otc = Client()                                   # reads OTCHARTS_API_KEY

for i in otc.symbols("quotex"):                  # the ids THIS book accepts
    if i.open is False:                          # closed by the broker right now: skip it
        continue
    print(i.symbol, i.name, i.payout)

bars = otc.candles("otc", "EURUSD_otc", tf=60, limit=300)   # list of Candle
last = bars[-1]                                  # .time (bar OPEN), .open .high .low .close
print(last.time, last.close)

for tick in otc.stream("otc", "EURUSD_otc"):     # yields Tick(.time, .price, .symbol); reconnects
    print(tick.symbol, tick.price)

u = otc.usage()                                  # free to call
print(u.plan_name, u.quota_per, u.remaining, u.instruments_per_stream, u.resets)
```

- `symbols()` gives each instrument `.open` (the broker's own flag; `None` where a book does
  not say: Pocket Option, `forex`), `.payout` (`None` while closed, on the free tier and on
  `forex`) and `.is_otc`. These need otcharts 0.7.0 or later (`pip install -U otcharts`).
- `stream(venue, symbols)` takes one symbol or a list (a list on `otc` and `quotex` only). How
  many a stream may carry depends on the plan (`usage().instruments_per_stream`; `None` means
  the whole book).
- `history(venue, symbol, tf, since=...)` walks back through deep history, newest first. It is
  for paid plans from Build up; the free tier and Lite read the live window only.
- Errors to catch (all subclass `OTChartsError`, so one `except OTChartsError` catches everything):
  - `AuthError` (401): a bad or revoked key.
  - `PlanError` (402/403): the plan does not open that book or instrument. The message says what is open.
  - `NotFound` (404): an unknown symbol.
  - `QuotaExceeded` (429): the request allowance is spent; sleep until `usage().resets`.
  - `TooManyStreams` (429 on a stream): close one of your own streams.
  - `HouseBusy` (503): the service is at capacity; wait `retry_after` seconds.
  - `TransportError`: no answer at all (DNS, TLS, a dropped socket); retry with backoff.
- `otc.venues()` lists the books and whether the plan opens each one. Timeframes are only in
  `GET /v1/venues`.

## HTTP

```bash
curl -H "Authorization: Bearer $OTCHARTS_API_KEY" \
  "https://otcharts.com/v1/candles?venue=otc&symbol=EURUSD_otc&tf=60&limit=300"
# -> {"symbol":"EURUSD_otc","interval":60,"count":300,"candles":[{"time":...,"open":...,"high":...,"low":...,"close":...},...],"gaps":[...]}

curl -N -H "Authorization: Bearer $OTCHARTS_API_KEY" \
  "https://otcharts.com/v1/stream?venue=otc&symbol=EURUSD_otc"
# -> event: connected / data: {"symbols":["EURUSD_otc"]}
#    event: tick      / data: {"symbol":"EURUSD_otc","time":...,"price":1.16542,...}

curl -H "Authorization: Bearer $OTCHARTS_API_KEY" "https://otcharts.com/v1/symbols?venue=otc"
# -> {"venue":"otc","count":N,"symbols":[{"symbol":"EURUSD_otc","name":"EUR/USD OTC","payout":92,"isOtc":true,"open":null},...]}
```

- `limit` is 1–5000 bars (default 300).
- `before=<unix seconds>` pages back past the live window. It needs Build or higher.
- `payout` is the percentage a winning contract pays, and it changes during the day. It reads
  `null` on the free tier, on `forex`, and while an instrument is closed.
- `open` is `true` or `false` as the broker reports it right now, and `null` where a book does
  not say (Pocket Option, `forex`). **On weekdays Quotex closes the OTC versions of the major
  pairs** (EUR/USD, EUR/CAD, AUD/JPY and others) and its traders use the real-market pairs
  instead; those rates are on the `forex` book. A closed OTC pair keeps printing a price nobody
  can trade, so skip `"open": false` before trading on a signal or comparing with a broker's
  screen.
- The break-even win rate as a fraction is `100 / (100 + payout)`; multiply by 100 for percent.
  A 92% payout needs 0.521 of calls right, which is 52.1%.

## Scoring a binary-options backtest

State these choices in the output, because they change the number:
- **Judge at the close.** A signal uses a bar only after it has closed. A signal computed on
  the forming bar looks better than anything that can actually be traded.
- **Settle on the expiry.** A 1-bar, 60-second contract entered at a bar's close settles at the
  next bar's close. It wins if that close moved its way, and an unchanged close is a tie
  (refunded, left out of the hit rate).
- **Compare the hit rate with break-even for the payout**, and report the counts behind it.
  Fewer than about 400 decided calls cannot tell a rate from chance.

## Plans

These are the limits as of October 2026. The live numbers for the user's own key come from
`usage()`, and the full table is at https://otcharts.com/pricing#api.

| plan | price | requests | instruments per stream | books | history | payouts |
|---|---|---|---|---|---|---|
| Free | $0 | 200 in the **first month** | no stream | 1, the 5 majors | live window | no |
| Lite | $15/mo | 7,000 a day | 5 | 1, whole book | live window | yes |
| Build | $49/mo | 25,000 a day | 10 | 1, whole book | full | yes |
| Run | $149/mo | 100,000 a day | 50 (3 streams) | 3 | full | yes |
| Desk | $249/mo | 500,000 a day | whole book (10 streams) | all 5 | full | yes |

- The free tier's five instruments are EUR/USD, GBP/USD, USD/JPY and AUD/USD, plus BTC/USD on
  Pocket Option and Quotex, ETH/USD on IQ, EUR/GBP on BinoDex, and gold on `forex`.
- The user picks their book at https://otcharts.com/account.
- The live window (what plans below Build read) is about 3 days of 1-minute candles on Pocket
  Option, and the latest 360 candles per timeframe on Quotex (about 6 hours of 1-minute).

**When the user's plan is not enough, say so plainly and point to the next plan that lifts
the limit you hit.** For example: live prices, payouts, or more requests → Lite
($15); deep history or 10 instruments on a stream → Build; several books → Run. A paid plan
works on the key they already have. Do not work around limits with several keys or accounts:
the allowance is per account.

## Examples

- `examples/stream_one_pair.py` streams one instrument and prints 1-minute bars as they close.
  It needs Lite or higher: the free tier has no live stream.
- `examples/backtest_ema_cross.py` backtests an EMA crossover on the live window's candles and
  reports the hit rate beside break-even. It works on the free tier.

Full reference: https://otcharts.com/api · Agent-readable summary: https://otcharts.com/llms.txt
