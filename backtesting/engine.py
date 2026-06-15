"""
Walk-forward backtesting engine with realistic execution.
Simulates actual trading with slippage, commissions, and position management.
"""

import pandas as pd
import numpy as np
import logging
import json
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass, asdict
from config.settings import BACKTEST_CONFIG, get_label_params

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Trade:
    """Represents a single trade."""
    entry_time: pd.Timestamp
    entry_price: float
    exit_time: pd.Timestamp
    exit_price: float
    direction: str  # 'long' or 'short'
    pnl_pct: float
    pnl_usd: float
    hit_tp: bool
    hit_sl: bool


class BacktestEngine:
    """Backtesting engine with realistic execution."""
    
    def __init__(self, 
                 initial_capital: float = None,
                 risk_per_trade: float = None,
                 commission_pct: float = None,
                 slippage_pct: float = None,
                 asset: str = "gold"):
        
        config = BACKTEST_CONFIG
        label_params = get_label_params(asset)
        
        self.initial_capital = initial_capital or config['initial_capital']
        self.risk_per_trade = risk_per_trade or config['risk_per_trade_usd']
        self.commission = commission_pct or config['commission_pct']
        self.slippage = slippage_pct or config['slippage_pct']
        
        self.tp_pct = label_params['take_profit_pct']
        self.sl_pct = label_params['stop_loss_pct']
        self.max_bars = label_params['max_bars']
        self.asset = asset
        
        self.trades: List[Trade] = []
        self.equity_curve = []
        
    def simulate_trade(self, 
                      entry_idx: int,
                      df: pd.DataFrame,
                      signal: int) -> Trade:
        """
        Simulate a single trade with realistic execution.
        
        Args:
            entry_idx: Index in dataframe where signal occurs
            df: Price dataframe
            signal: 1 for long, 0 for no trade
        
        Returns:
            Trade object with results
        """
        if signal == 0:
            return None
        
        # Entry on next bar (can't trade on signal bar)
        if entry_idx + 1 >= len(df):
            return None
        
        entry_time = df.index[entry_idx + 1]
        entry_price = df.iloc[entry_idx + 1]['open']
        
        # Apply slippage (assume we pay slippage on entry)
        entry_price *= (1 + self.slippage)
        
        # Look ahead for exit
        for k in range(1, self.max_bars + 1):
            exit_idx = entry_idx + 1 + k
            
            if exit_idx >= len(df):
                break
            
            current_bar = df.iloc[exit_idx]
            
            # Check if TP or SL hit during this bar
            high = current_bar['high']
            low = current_bar['low']
            
            ret_at_high = (high - entry_price) / entry_price
            ret_at_low = (low - entry_price) / entry_price
            
            hit_tp = ret_at_high >= self.tp_pct
            hit_sl = ret_at_low <= -self.sl_pct
            
            if hit_tp:
                # Exit at TP
                exit_price = entry_price * (1 + self.tp_pct)
                exit_price *= (1 - self.slippage)  # Slippage on exit
                pnl_pct = self.tp_pct - 2 * self.slippage - self.commission
                
                # Calculate USD P&L based on risk
                pnl_usd = (pnl_pct / abs(self.sl_pct)) * self.risk_per_trade
                
                return Trade(
                    entry_time=entry_time,
                    entry_price=entry_price,
                    exit_time=current_bar.name,
                    exit_price=exit_price,
                    direction='long',
                    pnl_pct=pnl_pct,
                    pnl_usd=pnl_usd,
                    hit_tp=True,
                    hit_sl=False
                )
            
            elif hit_sl:
                # Exit at SL
                exit_price = entry_price * (1 - self.sl_pct)
                exit_price *= (1 - self.slippage)
                pnl_pct = -self.sl_pct - 2 * self.slippage - self.commission
                
                pnl_usd = (pnl_pct / abs(self.sl_pct)) * self.risk_per_trade
                
                return Trade(
                    entry_time=entry_time,
                    entry_price=entry_price,
                    exit_time=current_bar.name,
                    exit_price=exit_price,
                    direction='long',
                    pnl_pct=pnl_pct,
                    pnl_usd=pnl_usd,
                    hit_tp=False,
                    hit_sl=True
                )
        
        # Timeout - exit at close of last bar
        else:
            if entry_idx + 1 + self.max_bars < len(df):
                exit_idx = entry_idx + 1 + self.max_bars
                exit_price = df.iloc[exit_idx]['close']
                exit_price *= (1 - self.slippage)
                
                pnl_pct = (exit_price - entry_price) / entry_price - self.commission
                pnl_usd = (pnl_pct / abs(self.sl_pct)) * self.risk_per_trade
                
                return Trade(
                    entry_time=entry_time,
                    entry_price=entry_price,
                    exit_time=df.index[exit_idx],
                    exit_price=exit_price,
                    direction='long',
                    pnl_pct=pnl_pct,
                    pnl_usd=pnl_usd,
                    hit_tp=False,
                    hit_sl=False
                )
        
        return None
    
    def run_backtest(self, df: pd.DataFrame, signals: np.ndarray) -> Dict:
        """
        Run complete backtest on test data.
        
        Args:
            df: Price dataframe (must have OHLC)
            signals: Array of trading signals (1 = trade, 0 = no trade)
        
        Returns:
            Dictionary with backtest results
        """
        logger.info("Running backtest...")
        
        self.trades = []
        equity = self.initial_capital
        self.equity_curve = [equity]
        
        # Simulate each trade
        for i, signal in enumerate(signals):
            if signal == 1:
                trade = self.simulate_trade(i, df, signal)
                
                if trade is not None:
                    self.trades.append(trade)
                    equity += trade.pnl_usd
                    self.equity_curve.append(equity)
        
        # Calculate metrics
        metrics = self.calculate_metrics()
        
        logger.info(f"Backtest complete: {len(self.trades)} trades executed")
        logger.info(f"Final equity: ${equity:.2f} ({(equity/self.initial_capital - 1)*100:+.1f}%)")
        
        results = {
            'trades': self.trades,
            'equity_curve': self.equity_curve,
            'metrics': metrics
        }
        
        # Save results as JSON
        self.save_results(results, df)
        
        return results
    
    def save_results(self, results: Dict, df: pd.DataFrame):
        """Save backtest results to JSON for dashboard."""
        output_dir = Path('reports/backtest_results')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Convert trades to serializable format
        trades_list = []
        for trade in results['trades']:
            trade_dict = asdict(trade)
            trade_dict['entry_time'] = trade.entry_time.isoformat()
            trade_dict['exit_time'] = trade.exit_time.isoformat()
            trades_list.append(trade_dict)
        
        # Prepare equity curve with timestamps
        equity_data = []
        trade_idx = 0
        for i, equity in enumerate(results['equity_curve']):
            if i == 0:
                timestamp = df.index[0].isoformat()
            elif trade_idx < len(results['trades']):
                timestamp = results['trades'][trade_idx].exit_time.isoformat()
                trade_idx += 1
            else:
                timestamp = df.index[-1].isoformat()
            
            equity_data.append({
                'timestamp': timestamp,
                'equity': float(equity)
            })
        
        # Session-wise performance
        session_performance = self.calculate_session_performance(results['trades'])
        
        # Save to JSON
        output = {
            'summary': results['metrics'],
            'equity_curve': equity_data,
            'trades': trades_list,
            'session_performance': session_performance
        }
        
        output_file = output_dir / f'{self.asset}_backtest.json'
        with open(output_file, 'w') as f:
            json.dump(output, f, indent=2)
        
        latest_file = output_dir / 'latest.json'
        with open(latest_file, 'w') as f:
            json.dump(output, f, indent=2)
        
        logger.info(f"Saved backtest results to {output_file}")
    
    def calculate_session_performance(self, trades: List[Trade]) -> Dict:
        """Calculate performance by trading session."""
        sessions = {'Asian': [], 'London': [], 'NY': []}
        
        for trade in trades:
            hour = trade.entry_time.hour
            
            # Classify session (simplified)
            if 0 <= hour < 8:
                session = 'Asian'
            elif 8 <= hour < 13:
                session = 'London'
            else:
                session = 'NY'
            
            sessions[session].append(trade.pnl_usd)
        
        # Calculate metrics per session
        session_stats = {}
        for session, pnls in sessions.items():
            if pnls:
                session_stats[session] = {
                    'trades': len(pnls),
                    'total_pnl': float(sum(pnls)),
                    'avg_pnl': float(np.mean(pnls)),
                    'win_rate': float(sum(1 for p in pnls if p > 0) / len(pnls))
                }
            else:
                session_stats[session] = {
                    'trades': 0,
                    'total_pnl': 0.0,
                    'avg_pnl': 0.0,
                    'win_rate': 0.0
                }
        
        return session_stats
    
    def calculate_metrics(self) -> Dict:
        """Calculate performance metrics."""
        if not self.trades:
            return {}
        
        pnls = [t.pnl_usd for t in self.trades]
        
        # Basic metrics
        n_trades = len(self.trades)
        wins = [t for t in self.trades if t.pnl_usd > 0]
        losses = [t for t in self.trades if t.pnl_usd <= 0]
        
        win_rate = len(wins) / n_trades if n_trades > 0 else 0
        avg_win = np.mean([t.pnl_usd for t in wins]) if wins else 0
        avg_loss = np.mean([t.pnl_usd for t in losses]) if losses else 0
        
        profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else np.inf
        
        # Returns
        total_return = sum(pnls)
        total_return_pct = (total_return / self.initial_capital) * 100
        
        # Risk metrics
        equity_series = pd.Series(self.equity_curve)
        drawdown = (equity_series / equity_series.cummax() - 1)
        max_drawdown = drawdown.min()
        max_drawdown_pct = max_drawdown * 100
        
        # Sharpe ratio (annualized, assuming 252 trading days)
        if len(pnls) > 1:
            returns = pd.Series(pnls) / self.initial_capital
            sharpe = (returns.mean() / returns.std()) * np.sqrt(252) if returns.std() != 0 else 0
        else:
            sharpe = 0
        
        # Sortino ratio (only downside deviation)
        if len(pnls) > 1:
            returns = pd.Series(pnls) / self.initial_capital
            downside_returns = returns[returns < 0]
            downside_std = downside_returns.std() if len(downside_returns) > 0 else 0
            sortino = (returns.mean() / downside_std) * np.sqrt(252) if downside_std != 0 else np.inf
        else:
            sortino = 0
        
        # Calmar ratio (annual return / max drawdown)
        # Assuming ~250 trading days per year
        days_trading = len(self.trades)  # Rough estimate
        annual_return = (total_return_pct / 100) * (250 / max(days_trading, 1))
        calmar = annual_return / abs(max_drawdown) if max_drawdown != 0 else np.inf
        
        return {
            'n_trades': n_trades,
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'total_return_usd': total_return,
            'total_return_pct': total_return_pct,
            'max_drawdown_pct': max_drawdown_pct,
            'sharpe_ratio': sharpe,
            'sortino_ratio': sortino,
            'calmar_ratio': calmar
        }
    
    def print_summary(self):
        """Print backtest summary."""
        metrics = self.calculate_metrics()
        
        print("\n" + "=" * 60)
        print("BACKTEST SUMMARY")
        print("=" * 60)
        print(f"Initial Capital:    ${self.initial_capital:,.2f}")
        print(f"Final Equity:       ${self.equity_curve[-1]:,.2f}")
        print(f"Total Return:       {metrics['total_return_pct']:+.2f}%")
        print(f"")
        print(f"Total Trades:       {metrics['n_trades']}")
        print(f"Win Rate:           {metrics['win_rate']:.1%}")
        print(f"Avg Win:            ${metrics['avg_win']:.2f}")
        print(f"Avg Loss:           ${metrics['avg_loss']:.2f}")
        print(f"Profit Factor:      {metrics['profit_factor']:.2f}")
        print(f"")
        print(f"Max Drawdown:       {metrics['max_drawdown_pct']:.2f}%")
        print(f"Sharpe Ratio:       {metrics['sharpe_ratio']:.2f}")
        print(f"Sortino Ratio:      {metrics['sortino_ratio']:.2f}")
        print(f"Calmar Ratio:       {metrics['calmar_ratio']:.2f}")
        print(f"Sharpe Ratio:       {metrics['sharpe_ratio']:.2f}")
        print("=" * 60)


if __name__ == "__main__":
    print("Backtesting engine ready.")
    print("Use BacktestEngine().run_backtest(df, signals) to test strategies.")
