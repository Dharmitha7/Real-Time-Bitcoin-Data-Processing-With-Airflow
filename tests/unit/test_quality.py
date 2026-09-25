import pandas as pd
import pandera.errors
import pytest

from bitcoin_pipeline import quality


def _write_csv(path, rows):
    pd.DataFrame(rows).to_csv(path, index=False)


def test_run_quality_checks_passes_for_valid_data(tmp_path):
    raw_path = tmp_path / "raw.csv"
    _write_csv(
        raw_path,
        [
            {
                "timestamp": "2026-01-01T00:00:00+00:00",
                "price_usd": 100.0,
                "change_1h": 1.0,
                "change_24h": 2.0,
            },
            {
                "timestamp": "2026-01-01T01:00:00+00:00",
                "price_usd": 101.0,
                "change_1h": 1.0,
                "change_24h": 2.0,
            },
        ],
    )

    quality.run_quality_checks(str(raw_path))  # should not raise


def test_run_quality_checks_rejects_negative_price(tmp_path):
    raw_path = tmp_path / "raw.csv"
    _write_csv(raw_path, [{"timestamp": "2026-01-01T00:00:00+00:00", "price_usd": -5.0}])

    with pytest.raises(pandera.errors.SchemaErrors):
        quality.run_quality_checks(str(raw_path))


def test_run_quality_checks_rejects_null_price(tmp_path):
    raw_path = tmp_path / "raw.csv"
    _write_csv(raw_path, [{"timestamp": "2026-01-01T00:00:00+00:00", "price_usd": None}])

    with pytest.raises(pandera.errors.SchemaErrors):
        quality.run_quality_checks(str(raw_path))


def test_run_quality_checks_rejects_missing_timestamp_column(tmp_path):
    raw_path = tmp_path / "raw.csv"
    pd.DataFrame([{"price_usd": 100.0}]).to_csv(raw_path, index=False)

    with pytest.raises(ValueError):
        quality.run_quality_checks(str(raw_path))


def test_run_quality_checks_rejects_large_timestamp_gap(tmp_path):
    raw_path = tmp_path / "raw.csv"
    _write_csv(
        raw_path,
        [
            {"timestamp": "2026-01-01T00:00:00+00:00", "price_usd": 100.0},
            {"timestamp": "2026-01-02T12:00:00+00:00", "price_usd": 101.0},
        ],
    )

    with pytest.raises(ValueError, match="Timestamp gap"):
        quality.run_quality_checks(str(raw_path))
