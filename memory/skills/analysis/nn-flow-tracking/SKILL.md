---
name: nn-flow-tracking
description: Track foreign-investor rotation across sectors and specific stocks, detect accumulation or distribution patterns, and project the next flow move based on catalyst timing. Best used weekly across a linked 5-10 session window.
category: stock-strategy
published: true
---

# NN Flow Tracking - Mapping Foreign-Capital Rotation

# NN Flow Tracking — Foreign Capital Flow Chaining

## Purpose
Track foreign capital rotation across sectors and individual stocks, detect accumulation/distribution patterns, and predict next moves based on the catalyst timeline.

## Frequency: Weekly (end of week or Monday morning)

## Process

### Step 1: Gather data (last 5-10 sessions)
- Source: CafeF (cafef.vn/du-lieu/lich-su-giao-dich/hose/{symbol}-3.chn) — Foreign tab
- Collect for: All portfolio + watchlist names + sector representatives (VCB for banks, VIC for Vingroup, FPT for IT, VHM for real estate, BSR for oil & gas)
- Data needed: Date, net volume, net value (billion VND), closing price

### Step 2: Chain patterns per stock
Divide into phases (3-5 sessions each):
- ACCUMULATE: ≥3 consecutive net buy sessions or strong cumulative positive
- DISTRIBUTE: ≥3 consecutive net sell sessions or strong cumulative negative
- SWING: Mixed buy/sell, no clear trend
- CATALYST SPIKE: Sharp buy/sell 1-2 sessions tied to an event

### Step 3: Capital rotation — track where foreign money is going
- Sector groups: Securities, Banks, Steel, Real Estate, IT, Oil & Gas, Consumer
- Sum foreign net by GROUP (not just individual stocks)
- Compare this week vs last week: Which group is money ROTATING FROM → TO?
- Common rotation patterns: Risk-off (sell securities/steel → buy banks/consumer) vs Risk-on (opposite)

### Step 4: Compare with Catalyst Timeline
- Map foreign flow against upcoming events (FTSE Sep, HRC 4/17, Q1 earnings, etc.)
- Foreign flow typically positions AHEAD of catalysts by 1-2 weeks
- For major index upgrade/rebalancing events, distinguish 2 layers of capital:
  - **Active / pre-positioning flow**: enters early, 1-12 weeks before event, selective buying in beneficiary stocks
  - **Passive / index flow**: enters at official rebalancing date, usually concentrated on effective day
- Remember the "FTSE paradox": before EM passive capital enters, frontier funds may have to sell first because the benchmark changed. Therefore, short-term net selling does not automatically negate the long-term thesis.

### Step 5: Assessment & Recommendation
- Which sector is foreign flow currently favoring?
- Any stock being sold by foreigners but price is not falling? (= strong domestic demand, potential reversal)
- Any stock foreigners are accumulating heavily but price hasn't moved much yet? (= accumulation not yet complete)
- Is this ETF/passive rebalancing or real active accumulation? Check block trades, even multi-session buying, and spread within the same sector.
- Recommendation: Should you follow foreign flow or be contrarian?

### Step 6: Macro Liquidity Overlay — Never read NN flow in a vacuum
Before concluding to follow the flow, mandatory overlay:
- O/N interbank rate: >5.5% = tight liquidity; >6% = stronger risk-off for banks/securities
- USD/VND exchange rate and official/free market spread: high spread = risk of NHNN tightening harder
- CPI / oil / macro shocks: if oil >$110 or CPI significantly exceeds target, reduce confidence in short-term risk-on thesis

**Implications**:
- Good foreign flow but tight domestic liquidity → rally may be weak or fail early
- Foreign net selling during benchmark restructuring transition but long-term catalyst intact → do not overreact to individual sessions

### Output format
Summary table + chained assessment in timeline format, with capital rotation chart (text-based).

## Benchmark patterns detected (15/4/2026)
- SSI: "Sell rally, buy dip, double down catalyst"
- HCM: "One-directional accumulation from bottom" (+239.8B cumulative over 20 sessions)
- TCB: "Binary event play — ignore → all-in"
- MBB: "Long-term sell → reversal" (-672B → +289.5B in last 3 sessions)
- HPG: "Coiling waiting for catalyst"

## Notes
- Looking at daily NN = NOISE. Chain 5-10 sessions to see the real pattern.
- NN buy/sell can be due to ETF rebalancing, passive fund flow, or active positioning — distinguish using spike volume vs steady buying.
- Combine with price + technical data to confirm (foreign accumulation + price breakout = strong signal).
- When you see a stock being net sold but price holds or bounces immediately, do not immediately conclude "foreign flow is wrong"; check whether domestic/prop demand is absorbing the entire selling.
- Prefer reading flow by sector cluster and time sequence; do not decide based on a single session of top buy/top sell.
