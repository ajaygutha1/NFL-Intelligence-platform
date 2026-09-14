# Learning Notes

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
