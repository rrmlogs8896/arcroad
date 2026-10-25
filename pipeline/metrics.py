"""HMA metrics, and the reporting rules that govern them.

The headline rule exists because v0.5 broke it: a review threshold was used to
filter the distribution rather than to mark points, and the published median
was computed on the surviving two thirds. headline_stats() takes the full set
and refuses to silently drop anything.
"""

import math

DI_SEVERE_DEFAULT = 5.0
DI_REVIEW_DEFAULT = 50.0


def pct(a, b) -> float:
    """Percentage, guarded against division by zero."""
    return round(100.0 * a / b, 1) if b else 0.0


def detour_index(network_m, straight_m):
    """Network distance divided by straight-line distance.

    Returns None when the pair is degenerate or the destination was not
    reachable within the routing limit. None means 'no measurement', never
    'zero detour'.
    """
    if straight_m is None or straight_m <= 0:
        return None
    if network_m is None:
        return None
    try:
        if not math.isfinite(network_m):
            return None
    except TypeError:
        return None
    return network_m / straight_m


def _median(values):
    s = sorted(values)
    n = len(s)
    if n == 0:
        return None
    mid = n // 2
    return s[mid] if n % 2 else (s[mid - 1] + s[mid]) / 2.0


def _quantile(values, q):
    s = sorted(values)
    if not s:
        return None
    idx = min(len(s) - 1, max(0, int(round(q * (len(s) - 1)))))
    return s[idx]


def headline_stats(values, di_review=DI_REVIEW_DEFAULT, di_severe=DI_SEVERE_DEFAULT):
    """Summary statistics over EVERY measured value.

    `di_review` marks points for verification. It must never remove them from
    the headline. The censored comparison is returned alongside so the effect
    of excluding high values is visible rather than hidden.
    """
    vals = [v for v in values if v is not None]
    if not vals:
        return {"n": 0}
    censored = [v for v in vals if v < di_review]
    return {
        "n": len(vals),
        "median": _median(vals),
        "p75": _quantile(vals, 0.75),
        "p90": _quantile(vals, 0.90),
        "max": max(vals),
        "pct_over_severe": pct(sum(1 for v in vals if v >= di_severe), len(vals)),
        "n_flagged": sum(1 for v in vals if v >= di_review),
        "pct_flagged": pct(sum(1 for v in vals if v >= di_review), len(vals)),
        # for transparency only — never the published figure
        "censored_median": _median(censored),
        "censored_n": len(censored),
    }


def worst_n(records, n=15, key="detour_index"):
    """The genuinely worst records, drawn from the uncensored set.

    v0.5 built this list after excluding everything above the review
    threshold, so every entry sat just below the cutoff and the table listed
    the points nearest the threshold rather than the worst ones.
    """
    scored = [r for r in records if r.get(key) is not None]
    return sorted(scored, key=lambda r: r[key], reverse=True)[:n]
