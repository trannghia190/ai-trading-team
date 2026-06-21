# Regression Case Library

Use this reference to test the routine report after each patch, especially when changing:
- regime logic
- emotion overlay
- shortlist filter
- action vocabulary
- scoring / penalty matrix

## What to check in each case
- Does the report produce a clear regime verdict?
- Is the emotion read calibrated correctly?
- Does the action table avoid forcing buy names when the market is unsuitable?
- Does it successfully remove illiquid noise?
- Is the language consistent with the canonical action vocabulary?

## Core archetypes
1. Broad risk-on with healthy breadth
2. Narrow index-led rally / green index with weak internals
3. Mixed rotational session
4. Risk-off / distribution day
5. Speculative froth without breadth support
6. Good stock, bad entry
7. Sector leader but flow conflict
8. Illiquid false positive
9. Broad risk-on but already crowded
10. Thesis intact, market ugly

## Minimum pack after any important patch
- Case 2
- Case 4
- Case 5
- Case 8

## Why this pack matters
- Case 2 checks whether the skill gets fooled by the index
- Case 4 checks whether the skill forces buy ideas
- Case 5 checks whether penny or speculative tape drags the skill off course
- Case 8 checks whether the liquidity floor and penalty matrix are working

## Reporting note
The routine report does not need to show the case name to the user.
This case library is for internal QA before trusting production output.
