"""Unit tests for backtesting.export module."""
import sys
import os
import json
import tempfile
from pathlib import Path

import pytest
import pandas as pd
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backtesting.export import BacktestExporter


@pytest.fixture
def sample_backtest_data():
    """Sample backtest results for export testing."""
    return {
        "summary": {
            "n_trades": 50,
            "win_rate": 0.6,
            "avg_win": 7.5,
            "avg_loss": -4.5,
            "profit_factor": 1.67,
            "total_return_usd": 150.0,
            "total_return_pct": 15.0,
            "max_drawdown_pct": -8.5,
            "sharpe_ratio": 2.1,
            "sortino_ratio": 2.8,
            "calmar_ratio": 1.76,
        },
        "trades": [
            {
                "entry_time": "2024-01-15T10:00:00",
                "entry_price": 2050.0,
                "exit_time": "2024-01-15T10:15:00",
                "exit_price": 2060.0,
                "direction": "long",
                "pnl_pct": 0.005,
                "pnl_usd": 7.5,
                "hit_tp": True,
                "hit_sl": False,
            },
            {
                "entry_time": "2024-01-15T11:00:00",
                "entry_price": 2055.0,
                "exit_time": "2024-01-15T11:15:00",
                "exit_price": 2048.0,
                "direction": "long",
                "pnl_pct": -0.0015,
                "pnl_usd": -4.5,
                "hit_tp": False,
                "hit_sl": True,
            },
            {
                "entry_time": "2024-01-15T14:00:00",
                "entry_price": 2040.0,
                "exit_time": "2024-01-15T14:15:00",
                "exit_price": 2052.0,
                "direction": "long",
                "pnl_pct": 0.005,
                "pnl_usd": 12.0,
                "hit_tp": True,
                "hit_sl": False,
            },
        ],
        "equity_curve": [
            {"timestamp": "2024-01-15T10:00:00", "equity": 1000.0},
            {"timestamp": "2024-01-15T10:15:00", "equity": 1007.5},
            {"timestamp": "2024-01-15T11:15:00", "equity": 1003.0},
            {"timestamp": "2024-01-15T14:15:00", "equity": 1015.0},
        ],
    }


class TestBacktestExporter:
    """Test BacktestExporter class."""

    def test_exporter_initialization(self):
        exporter = BacktestExporter()
        assert exporter is not None

    def test_export_trades_csv(self, sample_backtest_data, tmp_path):
        exporter = BacktestExporter()
        output_path = tmp_path / "trades.csv"
        result = exporter.export_trades_csv(sample_backtest_data, str(output_path))
        assert result is True
        assert output_path.exists()
        df = pd.read_csv(output_path)
        assert len(df) == 3
        assert "entry_time" in df.columns
        assert "pnl_usd" in df.columns

    def test_export_summary_csv(self, sample_backtest_data, tmp_path):
        exporter = BacktestExporter()
        output_path = tmp_path / "summary.csv"
        result = exporter.export_summary_csv(sample_backtest_data, str(output_path))
        assert result is True
        assert output_path.exists()
        df = pd.read_csv(output_path)
        assert len(df) == 1
        assert "win_rate" in df.columns
        assert "sharpe_ratio" in df.columns

    def test_export_equity_csv(self, sample_backtest_data, tmp_path):
        exporter = BacktestExporter()
        output_path = tmp_path / "equity.csv"
        result = exporter.export_equity_csv(sample_backtest_data, str(output_path))
        assert result is True
        assert output_path.exists()
        df = pd.read_csv(output_path)
        assert len(df) == 4
        assert "timestamp" in df.columns
        assert "equity" in df.columns

    def test_export_full_report_csv(self, sample_backtest_data, tmp_path):
        exporter = BacktestExporter()
        output = tmp_path / "report"
        result = exporter.export_full_report_csv(sample_backtest_data, str(output))
        assert result is True
        assert (tmp_path / "report_trades.csv").exists()
        assert (tmp_path / "report_summary.csv").exists()
        assert (tmp_path / "report_equity.csv").exists()

    def test_export_pdf(self, sample_backtest_data, tmp_path):
        exporter = BacktestExporter()
        output_path = tmp_path / "report.pdf"
        result = exporter.export_pdf(sample_backtest_data, str(output_path))
        assert result is True
        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_export_pdf_contains_text(self, sample_backtest_data, tmp_path):
        exporter = BacktestExporter()
        output_path = tmp_path / "report.pdf"
        exporter.export_pdf(sample_backtest_data, str(output_path))
        content = output_path.read_bytes()
        assert b"%PDF" in content[:10]

    def test_export_csv_empty_trades(self, tmp_path):
        exporter = BacktestExporter()
        data = {"summary": {"n_trades": 0}, "trades": [], "equity_curve": []}
        output_path = tmp_path / "empty.csv"
        result = exporter.export_trades_csv(data, str(output_path))
        assert result is True
        assert output_path.exists()

    def test_export_pdf_empty_trades(self, tmp_path):
        exporter = BacktestExporter()
        data = {"summary": {"n_trades": 0}, "trades": [], "equity_curve": []}
        output_path = tmp_path / "empty.pdf"
        result = exporter.export_pdf(data, str(output_path))
        assert result is True
        assert output_path.exists()

    def test_export_summary_csv_values(self, sample_backtest_data, tmp_path):
        exporter = BacktestExporter()
        output_path = tmp_path / "summary.csv"
        exporter.export_summary_csv(sample_backtest_data, str(output_path))
        df = pd.read_csv(output_path)
        assert df.iloc[0]["win_rate"] == 0.6
        assert df.iloc[0]["sharpe_ratio"] == 2.1
        assert df.iloc[0]["total_return_pct"] == 15.0

    def test_export_trades_csv_columns(self, sample_backtest_data, tmp_path):
        exporter = BacktestExporter()
        output_path = tmp_path / "trades.csv"
        exporter.export_trades_csv(sample_backtest_data, str(output_path))
        df = pd.read_csv(output_path)
        expected_cols = {"entry_time", "entry_price", "exit_time", "exit_price",
                         "direction", "pnl_pct", "pnl_usd", "hit_tp", "hit_sl"}
        assert expected_cols.issubset(set(df.columns))
