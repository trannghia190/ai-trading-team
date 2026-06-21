# Macro Liquidity Overlay

## Purpose

This reference adds a macro-liquidity layer to VN stock market reports so they can explain the national liquidity backdrop rather than stopping at price, breadth, and foreign flow.

## Use when

Use this when the report needs to explain why risk appetite is being supported or restrained by macro liquidity.

## Priority factors

### 1. SBV / OMO / liquidity operations
Track when data is available:
- net injection / net drain
- bills / repo / reverse repo
- size and tenor when available

Interpretation:
- prolonged net injection -> supportive
- prolonged net drain -> tightening headwind
- a sudden strong drain -> stress warning, especially if breadth is weak or FX is under pressure

### 2. Interbank rates
Track when data is available:
- overnight
- 1W or other short tenors if available

Interpretation:
- lower or stably low rates -> supportive or neutral
- rapidly rising rates -> tightening headwind
- overnight spike -> stress warning

### 3. Government bond yields
Track when data is available:
- 2Y / 5Y / 10Y, or at minimum 10Y
- daily-to-weekly direction

Interpretation:
- rapidly rising yields -> an equity headwind, especially for growth or duration-sensitive names
- stable or falling yields -> less discount-rate pressure

### 4. FX pressure
Track when data is available:
- USD/VND
- central reference rate if available
- DXY or broader USD backdrop if available

Interpretation:
- stable FX -> neutral or supportive
- heating USD/VND -> tightening headwind
- FX stress plus SBV liquidity withdrawal -> stronger stress warning

## Final macro verdict labels

Choose only one label:
- supportive
- neutral
- tightening headwind
- stress warning

## Interaction rules

- Broad risk-on plus supportive macro -> be more open to `BUY ON TRIGGER`.
- Mixed rotation plus neutral macro -> stay selective and do not over-upgrade.
- Breadth BEAR plus tightening headwind -> downgrade every new entry by one notch.
- Breadth BEAR plus stress warning -> `0 focus buy now` is a very valid conclusion.

## Reporting rule

If structured macro-liquidity data is missing:
- explicitly state that macro-liquidity evidence is partial
- do not hallucinate OMO, interbank, or bond data
- the report must still function using the market-structure evidence that is available
