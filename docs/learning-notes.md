# Learning Notes

## Sharat — Game Exploration (Task 1/2)

**Game:** 2023_01_ARI_WAS (Arizona @ Washington, Week 1, 2023)

**Highest positive EPA play (+2.96):** Howell threw a deep incomplete pass to
McLaurin, but Arizona was called for defensive pass interference (37 yards,
enforced at the 50). Even though the pass itself failed, the penalty gave
Washington a free 37-yard gain and an automatic first down from a much
better field position — which is why EPA rewards this play so heavily. EPA
measures the change in expected points, not just whether the throw was
completed.

**Highest negative EPA play (-7.30):** Howell was sacked for a 14-yard loss,
fumbled on the hit, and Arizona recovered and returned it for a touchdown.
This is close to the worst possible outcome for an offense on a single
play — not only did Washington lose yardage and possession, the turnover
directly became 7 points for Arizona. That combination (huge yardage loss +
turnover + defensive touchdown) is why this play has the most negative EPA
in the game.

## Session 3 — Feature coefficients vs. permutation importance

While comparing the logistic regression coefficients to permutation importance on
the holdout season, a few features that looked important by coefficient size didn't
show much drop in performance when permuted, and vice versa. This points to
multicollinearity between some of the rolling EPA features (e.g. `diff_off_epa` and
`diff_pass_epa`/`diff_rush_epa` are correlated, since offensive EPA is partly made up
of pass and rush EPA).

Takeaway: when features are correlated, a linear model can split credit between them
arbitrarily, so raw coefficient magnitude isn't a reliable importance signal on its
own — permutation importance (which measures actual predictive contribution) is the
more trustworthy of the two here. Doesn't change the model for V1, but worth keeping
in mind if features are added/pruned later.
