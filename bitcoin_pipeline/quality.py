"""Data-quality checks for the raw Bitcoin price CSV, run as a real (failing) Airflow task."""

import logging

import pandas as pd
import pandera.pandas as pa

logger = logging.getLogger(__name__)

BitcoinPriceSchema = pa.DataFrameSchema(
    {
        # No fixed dtype check here: pandas may parse ISO8601 timestamps as
        # datetime64[ns] or datetime64[us], tz-naive or tz-aware, depending on
        # version and input - we only care that it parsed as a datetime at all.
        "timestamp": pa.Column(
            nullable=False,
            checks=pa.Check(lambda s: pd.api.types.is_datetime64_any_dtype(s), element_wise=False),
        ),
        "price_usd": pa.Column(float, checks=pa.Check.gt(0), nullable=False),
        "change_1h": pa.Column(float, nullable=True, required=False),
        "change_24h": pa.Column(float, nullable=True, required=False),
    },
    strict=False,
)

MAX_EXPECTED_GAP = pd.Timedelta(hours=2)


def run_quality_checks(raw_path: str) -> None:
    """Validate schema and timestamp cadence of the raw CSV. Raises on any violation."""
    df = pd.read_csv(raw_path, parse_dates=["timestamp"])
    BitcoinPriceSchema.validate(df, lazy=True)

    if len(df) > 1:
        gaps = df["timestamp"].sort_values().diff().dropna()
        max_gap = gaps.max()
        if max_gap > MAX_EXPECTED_GAP:
            raise ValueError(
                f"Timestamp gap of {max_gap} in {raw_path} exceeds the expected hourly cadence."
            )

    logger.info(f"Data quality checks passed for {raw_path} ({len(df)} rows).")
