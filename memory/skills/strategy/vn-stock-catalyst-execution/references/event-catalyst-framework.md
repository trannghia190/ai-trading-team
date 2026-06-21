# Event Catalyst Framework

## Purpose
Standardize how catalysts and events should be interpreted for VN stocks using a stock-mcp-first approach.

## Event taxonomy
- Scheduled: earnings, AGM, ex-dividend, issuance, ETF rebalance, legal effective date
- Policy / macro: regulation, tax, tariff, commodity, rates, FX
- Stock-specific positive: contract, product, capacity, M&A, legal unlock
- Stock-specific negative: lawsuit, sanction, dilution, governance, delay

## Mandatory questions
1. What exactly is the event?
2. Does it mainly affect revenue, margin, valuation multiple, legal certainty, or only sentiment?
3. Is the effect intraday, a few sessions, a few weeks, or a few months?
4. Does the event affect only this stock, or the broader theme or sector as well?
5. Is the current price still near a base, or has it already run too far ahead?
6. Is flow confirming the move?
7. Does T+2 settlement lock-up make the trade less attractive?

## Catalyst state
- Unpriced / early recognition
- Partially priced
- Crowded / expectation-rich
- Stale / expired

## Priced-in clues
- Price has already risen for many consecutive sessions and sits far above the nearest support
- Headline heat is strong, but follow-through is weakening
- Turnover is abnormally high, but incremental reward is not keeping up
- Too many people are focused on the same story, and execution has become crowded

## Invalidation templates
- The catalyst points in the right direction, but the details are weaker than the narrative
- Follow-through is poor, the breakout fails, or price closes back below the confirmation zone
- Foreign selling or distribution appears after the event
- Foreign selling or distribution appears after the event
- The timeline is delayed or the legal wording is not strong enough
- Weak macro or market regime prevents the catalyst from getting the expected multiple

## Old-tool to Trading Team mapping
- search_stock_news -> get_market_hot_news / get_stock_news / get_stock_social_posts / search_stock_social_posts
- get_realtime_quote -> get_price_data / get_finpath_stock_snapshot
- analyze_trend -> get_technical_analysis
- get_daily_history -> get_ohlcv
