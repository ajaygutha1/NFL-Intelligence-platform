## Early-season rolling features

Rolling features require five previous games.

For each team's first five games of a season, the rolling-5 features
are left as NaN because five prior games are not available.

For the initial model, games without a complete five-game history will
not be used when rolling-5 features are required.

This keeps the amount of historical information consistent and ensures
that the current game's performance is never used to predict itself.

## Tied games

Tied games are excluded from the V1 prediction model.

The current target is binary:
- 1 = home team wins
- 0 = away team wins

A tied game does not belong to either class, so ties are removed
for the initial model.