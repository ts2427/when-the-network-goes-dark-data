"""Writing published CSVs: counts as nullable integers (42, not 42.0), the same bytes on every platform."""
from pathlib import Path

import pandas as pd


def as_counts(df: pd.DataFrame, cols) -> pd.DataFrame:
    """The given columns as pandas Int64 (blank stays blank; -0.0 becomes 0). Stops if a value is not whole."""
    out = df.copy()
    for c in cols:
        v = pd.to_numeric(out[c])
        frac = v.dropna() % 1
        if (frac != 0).any():
            raise SystemExit(f"{c}: not a count, {int((frac != 0).sum())} values are not whole")
        out[c] = v.round().astype("Int64")
    return out


def write_csv(df: pd.DataFrame, path: Path, counts=()) -> None:
    """index=False, '\\n' line ends, count columns as integers."""
    path.parent.mkdir(parents=True, exist_ok=True)
    as_counts(df, counts).to_csv(path, index=False, lineterminator="\n")
