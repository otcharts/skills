# OTCharts skills for AI agents

Give your coding agent (Claude Code, Codex, Cursor, Gemini CLI, OpenCode and
[40+ more](https://github.com/vercel-labs/skills)) working knowledge of the
[OTCharts](https://otcharts.com) market data API: OTC prices from Pocket Option, Quotex,
IQ Option and BinoDex, plus the real FX market, as candles, live ticks and payouts.

## 1. Install the skill

```bash
npx skills add otcharts/skills
```

## 2. Get a free key

Make one at [otcharts.com/account](https://otcharts.com/account) (no card needed), then:

```bash
export OTCHARTS_API_KEY=otc_live_...
```

## 3. Try a prompt

> Using the OTCharts skill, stream EUR/USD OTC from Pocket Option and print a 1-minute
> candle every time one closes.

> Using the OTCharts skill, backtest an EMA 9/21 crossover on the last 3 days of 1-minute
> candles for EURUSD_otc and show the hit rate beside the break-even for a 92% payout.

> Using the OTCharts skill, list every Pocket Option instrument with its payout and flag the
> ones whose break-even is above 55%.

> Using the OTCharts skill, compare EUR/USD OTC on Pocket Option and Quotex side by side and
> chart where the two brokers' prices part ways.

The first two prompts run on the free tier. The payout list needs Lite or higher, and the
two-broker comparison needs Run. The agent will say so when your plan falls short.

## What the agent learns

- How to authenticate, and the Python client (`pip install otcharts`) or plain HTTP.
- The five books and their symbol formats. `EURUSD_otc`, `EURUSD-OTC` and `EUR/USD-OTC` are
  not interchangeable.
- To stream live prices instead of polling candles, which is what keeps a bot inside its
  allowance.
- Every plan's limits and what each error means.

This reads prices only; it never places trades or needs a broker login. Not affiliated with
any broker named here.

Full API reference: [otcharts.com/api](https://otcharts.com/api) · Plans:
[otcharts.com/pricing](https://otcharts.com/pricing#api)
