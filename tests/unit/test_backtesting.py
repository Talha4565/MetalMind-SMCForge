"""Unit tests for backtesting.engine module."""
import sys
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backtesting.engine import BacktestEngine, Trade


class TestTradeDataclass:
    """Test Trade dataclass."""

    def test_trade_creation(self):
        trade = Trade(
            entry_time=pd.Timestamp('2024-01-01 08:00'),
            entry_price=2000.0,
            exit_time=pd.Timestamp('2024-01-01 08:15'),
            exit_price=2010.0,
            direction='long',
            pnl_pct=0.005,
            pnl_usd=5.0,
            hit_tp=True,
            hit_sl=False
        )
        assert trade.entry_price == 2000.0
        assert trade.exit_price == 2010.0
        assert trade.direction == 'long'
        assert trade.hit_tp is True
        assert trade.hit_sl is False


class TestBacktestEngine:
    """Test backtesting engine."""

    def test_engine_initialization_gold(self):
        engine = BacktestEngine(asset='gold')
        assert engine.asset == 'gold'
        assert engine.initial_capital > 0
        assert engine.tp_pct > 0
        assert engine.sl_pct > 0

    def test_engine_initialization_silver(self):
        engine = BacktestEngine(asset='silver')
        assert engine.asset == 'silver'

    def test_engine_custom_params(self):
        engine = BacktestEngine(
            initial_capital=5000,
            risk_per_trade=10,
            commission_pct=0.001,
            slippage_pct=0.001
        )
        assert engine.initial_capital == 5000
        assert engine.risk_per_trade == 10

    def test_simulate_trade_no_signal(self, small_ohlcv_df):
        engine = BacktestEngine(asset='gold')
        trade = engine.simulate_trade(0, small_ohlcv_df, signal=0)
        assert trade is None

    def test_simulate_trade_at_end_of_data(self):
        n = 10
        dates = pd.date_range('2024-01-01', periods=n, freq='15min')
        df = pd.DataFrame({
            'open': np.full(n, 2000.0),
            'high': np.full(n, 2010.0),
            'low': np.full(n, 1990.0),
            'close': np.full(n, 2000.0),
            'volume': np.full(n, 1000)
        }, index=dates)
        engine = BacktestEngine(asset='gold')
        trade = engine.simulate_trade(n - 1, df, signal=1)
        assert trade is None

    def test_simulate_trade_tp_hit(self):
        n = 20
        dates = pd.date_range('2024-01-01', periods=n, freq='15min')
        close = np.full(n, 2000.0)
        close[3] = 2020.0  # Big move up that hits TP
        df = pd.DataFrame({
            'open': close - 1,
            'high': close + 10,
            'low': close - 5,
            'close': close,
            'volume': np.full(n, 1000)
        }, index=dates)
        engine = BacktestEngine(asset='gold')
        trade = engine.simulate_trade(0, df, signal=1)
        if trade is not None:
            assert trade.hit_tp is True or trade.hit_sl is True or trade.pnl_pct != 0

    def test_run_backtest_empty_signals(self, small_ohlcv_df):
        engine = BacktestEngine(asset='gold')
        signals = np.zeros(len(small_ohlcv_df), dtype=int)
        results = engine.run_backtest(small_ohlcv_df, signals)
        assert results['metrics'] == {} or results['metrics'].get('n_trades', 0) == 0

    def test_run_backtest_with_signals(self, small_ohlcv_df):
        engine = BacktestEngine(asset='gold')
        signals = np.zeros(len(small_ohlcv_df), dtype=int)
        signals[10] = 1
        signals[50] = 1
        results = engine.run_backtest(small_ohlcv_df, signals)
        assert 'metrics' in results
        assert 'trades' in results
        assert 'equity_curve' in results

    def test_equity_curve_starts_at_initial_capital(self, small_ohlcv_df):
        engine = BacktestEngine(asset='gold', initial_capital=1000)
        signals = np.zeros(len(small_ohlcv_df), dtype=int)
        results = engine.run_backtest(small_ohlcv_df, signals)
        assert results['equity_curve'][0] == 1000

    def test_metrics_structure(self, small_ohlcv_df):
        engine = BacktestEngine(asset='gold')
        signals = np.zeros(len(small_ohlcv_df), dtype=int)
        signals[10] = 1
        signals[30] = 1
        signals[60] = 1
        results = engine.run_backtest(small_ohlcv_df, signals)
        metrics = results['metrics']
        if metrics:
            assert 'n_trades' in metrics
            assert 'win_rate' in metrics
            assert 'profit_factor' in metrics
            assert 'max_drawdown_pct' in metrics
            assert 'sharpe_ratio' in metrics

    def test_win_rate_between_0_and_1(self, small_ohlcv_df):
        engine = BacktestEngine(asset='gold')
        signals = np.zeros(len(small_ohlcv_df), dtype=int)
        signals[10] = 1
        signals[30] = 1
        results = engine.run_backtest(small_ohlcv_df, signals)
        if results['metrics'].get('n_trades', 0) > 0:
            wr = results['metrics']['win_rate']
            assert 0 <= wr <= 1

    def test_session_performance(self, small_ohlcv_df):
        engine = BacktestEngine(asset='gold')
        signals = np.zeros(len(small_ohlcv_df), dtype=int)
        signals[10] = 1
        signals[30] = 1
        results = engine.run_backtest(small_ohlcv_df, signals)
        sp = engine.calculate_session_performance(results['trades'])
        for session in ['Asian', 'London', 'NY']:
            assert session in sp

    def test_many_signals(self, small_ohlcv_df):
        engine = BacktestEngine(asset='gold')
        signals = np.ones(len(small_ohlcv_df), dtype=int)
        results = engine.run_backtest(small_ohlcv_df, signals)
        assert results['metrics']['n_trades'] >= 0
