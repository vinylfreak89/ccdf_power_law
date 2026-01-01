"""
Simple Backtest Engine

Backtests signals on price data with position sizing.
"""
import pandas as pd
import numpy as np


def run_backtest(df, initial_capital=10000):
    """
    Run backtest on dataframe with Signal column.
    
    Args:
        df: DataFrame with Date, Close, Return, Signal columns
        initial_capital: Starting capital
        
    Returns:
        dict with results and summary statistics
    """
    df = df.copy()
    df = df[df['Signal'].notna()].reset_index(drop=True)
    
    # Calculate strategy returns
    # Signal * Return gives position-weighted return
    df['StrategyReturn'] = df['Signal'] * df['Return']
    
    # Calculate cumulative returns
    df['CumReturn'] = (1 + df['Return'] / 100).cumprod()
    df['CumStrategyReturn'] = (1 + df['StrategyReturn'] / 100).cumprod()
    
    # Calculate portfolio value
    df['PortfolioValue'] = initial_capital * df['CumStrategyReturn']
    df['BuyHoldValue'] = initial_capital * df['CumReturn']
    
    # Calculate drawdown
    df['Peak'] = df['PortfolioValue'].cummax()
    df['Drawdown'] = (df['PortfolioValue'] - df['Peak']) / df['Peak'] * 100
    
    # Summary statistics
    total_return = (df['PortfolioValue'].iloc[-1] / initial_capital - 1) * 100
    bh_return = (df['BuyHoldValue'].iloc[-1] / initial_capital - 1) * 100
    
    strategy_returns = df['StrategyReturn'].dropna()
    sharpe = strategy_returns.mean() / strategy_returns.std() * np.sqrt(252) if strategy_returns.std() > 0 else 0
    
    max_dd = df['Drawdown'].min()
    
    # Count positions
    long_days = (df['Signal'] > 0).sum()
    short_days = (df['Signal'] < 0).sum()
    neutral_days = (df['Signal'] == 0).sum()
    
    summary = f"""
=== BACKTEST RESULTS ===

Period: {df['Date'].min()} to {df['Date'].max()}
Trading Days: {len(df)}

RETURNS:
  Strategy: {total_return:.2f}%
  Buy & Hold: {bh_return:.2f}%
  Outperformance: {total_return - bh_return:.2f}%

RISK:
  Sharpe Ratio: {sharpe:.3f}
  Max Drawdown: {max_dd:.2f}%

POSITIONS:
  Long days: {long_days} ({long_days/len(df)*100:.1f}%)
  Short days: {short_days} ({short_days/len(df)*100:.1f}%)
  Neutral days: {neutral_days} ({neutral_days/len(df)*100:.1f}%)

FINAL VALUES:
  Strategy: ${df['PortfolioValue'].iloc[-1]:,.2f}
  Buy & Hold: ${df['BuyHoldValue'].iloc[-1]:,.2f}
"""
    
    return {
        'df': df,
        'summary': summary,
        'metrics': {
            'total_return': total_return,
            'bh_return': bh_return,
            'sharpe': sharpe,
            'max_dd': max_dd,
            'final_value': df['PortfolioValue'].iloc[-1]
        }
    }
