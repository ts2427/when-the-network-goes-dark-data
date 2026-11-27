"""Compare two results.json trees: numbers within a relative tolerance, everything else exactly (v2.2.0).

Used by the reproduction test and the v1 results test, so that last-bit differences between platforms' floating-point
libraries (up to about 1e-9 relative) do not fail them, while any real change does.
"""
import math

RTOL = 1e-8  # 1e-9 until 2026-11-24: Linux CI differed by 1.2e-9 in a chapter 8 sensitivity interval
# Values that are zero by construction (e.g. an in-sample calibration-in-the-large) come out as floating-point noise
# around 1e-15 that differs between machines; no relative tolerance can match them. Numbers within ATOL match.
ATOL = 1e-12


def _is_num(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _is_nan(x) -> bool:
    return isinstance(x, float) and math.isnan(x)


def differences(got, want, rtol: float = RTOL, path: str = "", atol: float = ATOL) -> list:
    """Every place where got and want differ: a list of (path, got, want). Numbers compare with math.isclose(rel_tol=
    rtol, abs_tol=atol); an int and an equal float match. Strings, booleans, None, keys and list lengths must match."""
    # since 3.2.1 results.json writes a missing number as null instead of NaN (valid JSON); older snapshots hold NaN
    if (got is None and _is_nan(want)) or (want is None and _is_nan(got)):
        return []
    if _is_num(got) and _is_num(want):
        both_nan = isinstance(got, float) and isinstance(want, float) and math.isnan(got) and math.isnan(want)
        same = got == want or both_nan or math.isclose(got, want, rel_tol=rtol, abs_tol=atol)
        return [] if same else [(path, got, want)]
    if isinstance(got, dict) and isinstance(want, dict):
        if list(got) != list(want):
            return [(path + " (keys)", list(got), list(want))]
        return [d for k in want for d in differences(got[k], want[k], rtol, f"{path}/{k}", atol)]
    if isinstance(got, list) and isinstance(want, list):
        if len(got) != len(want):
            return [(path + " (length)", len(got), len(want))]
        return [d for i, (a, b) in enumerate(zip(got, want)) for d in differences(a, b, rtol, f"{path}[{i}]", atol)]
    if type(got) is not type(want) or got != want:
        return [(path, got, want)]
    return []


def max_relative(got, want) -> float:
    """The largest relative difference between matching numbers (for reporting)."""
    if _is_num(got) and _is_num(want):
        if got == want or not (math.isfinite(got) and math.isfinite(want)):
            return 0.0
        return abs(got - want) / max(abs(got), abs(want))
    if isinstance(got, dict) and isinstance(want, dict):
        return max([max_relative(got[k], want[k]) for k in want if k in got] or [0.0])
    if isinstance(got, list) and isinstance(want, list):
        return max([max_relative(a, b) for a, b in zip(got, want)] or [0.0])
    return 0.0
