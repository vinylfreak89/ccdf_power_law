"""
Backtest a signal with configurable lag (T+0, T+1, T+N).

T+0: Signal on day i applies to day i's return (same day)
T+1: Signal on day i applies to day i+1's return (next day)
T+N: Signal on day i applies to day i+N's return (N days later)
"""
import numpy as np
import pandas as pd


def backtest(df, lag=0, leverage_map=None):
    """
    Backtest a signal with configurable lag.
    
    Args:
        df: DataFrame with 'Return', 'State', and 'Signal_Modified' columns
        lag: Number of days to shift signal forward (0=T+0, 1=T+1, etc.)
        leverage_map: dict mapping state to leverage multiplier
                     Default: {'RED': 1.0, 'ORANGE': 1.0, 'GREEN': 2.0}
                     Or uses Signal_Modified if State not available
        
    Returns:
        DataFrame with added columns:
            - Position: Leverage multiplier for each day
            - Strategy_Return: Return * Position
            - BH_Cumulative: Buy & Hold cumulative value
            - Strategy_Cumulative: Strategy cumulative value
    """
    df = df.copy()
    
    # Default leverage map
    if leverage_map is None:
        leverage_map = {
            'RED': 1.0,
            'ORANGE': 1.0,
            'GREEN': 2.0
        }
    
    # Determine position based on State or Signal_Modified
    if 'State' in df.columns:
        # Map states to positions
        df['Position'] = df['State'].map(leverage_map)
        # Fill any unmapped states with default (2.0)
        df['Position'].fillna(2.0, inplace=True)
    elif 'Signal_Modified' in df.columns:
        # Binary signal: 1 = RED (1x), 0 = GREEN (2x)
        df['Position'] = np.where(df['Signal_Modified'] == 1, 1.0, 2.0)
    else:
        raise ValueError("DataFrame must have either 'State' or 'Signal_Modified' column")
    
    # Apply lag: shift position forward by N days
    if lag > 0:
        df['Position'] = df['Position'].shift(-lag)
        # Fill end with default position (2.0 = GREEN)
        df['Position'].fillna(2.0, inplace=True)
    
    # Calculate returns
    df['Strategy_Return'] = df['Return'] * df['Position']
    df['BH_Cumulative'] = (1 + df['Return']/100).cumprod()
    df['Strategy_Cumulative'] = (1 + df['Strategy_Return']/100).cumprod()
    
    # Summary stats
    final_bh = df['BH_Cumulative'].iloc[-1]
    final_strat = df['Strategy_Cumulative'].iloc[-1]
    ratio = final_strat / final_bh
    
    years = (df['Date'].iloc[-1] - df['Date'].iloc[0]).days / 365.25
    bh_cagr = (final_bh ** (1/years) - 1) * 100
    strat_cagr = (final_strat ** (1/years) - 1) * 100
    
    print(f"✓ Backtest (T+{lag}):")
    print(f"  Period: {df['Date'].iloc[0].date()} to {df['Date'].iloc[-1].date()} ({years:.1f} years)")
    print(f"  Buy & Hold: ${final_bh:,.2f} ({bh_cagr:.2f}% CAGR)")
    print(f"  Strategy:   ${final_strat:,.2f} ({strat_cagr:.2f}% CAGR)")
    print(f"  Ratio: {ratio:.2f}x")
    
    return df


if __name__ == '__main__':
    # Test it
    import sys
    sys.path.append('/mnt/user-data/outputs/code/data')
    sys.path.append('/mnt/user-data/outputs/code/signals')
    sys.path.append('/mnt/user-data/outputs/code/analysis')
    
    from load_data import load_asset
    from moderate_vol import calculate_signal
    from state_utils import combine_states
    
    print("Testing backtest on SPX...")
    df = load_asset('_spx_d.csv')
    df = calculate_signal(df)
    
    # Combine ORANGE with GREEN to match original Signal_Modified behavior
    df = combine_states(df, 'GREEN', ['ORANGE'])
    
    # Filter to valid days (after 2-year baseline)
    df_valid = df[df['Baseline'].notna()].copy()
    
    print("\nT+0 (same day trading):")
    df_t0 = backtest(df_valid, lag=0)
    
    print("\nT+1 (next day trading):")
    df_t1 = backtest(df_valid, lag=1)
    
    print("\nT+5 (5 days later):")
    df_t5 = backtest(df_valid, lag=5)
    
    # Verify against working code (plot_correct.py)
    print(f"\n{'='*60}")
    print("VALIDATION - Running working code for comparison...")
    print(f"{'='*60}")
    
    # Run plot_correct.py and capture output
    import subprocess
    result = subprocess.run(['python', '/home/claude/plot_correct.py'], 
                          capture_output=True, text=True, cwd='/home/claude')
    
    # Extract T+0 and T+1 values from output
    import re
    t0_match = re.search(r'Strategy T\+0:\s+\$[\d,]+\.\d+\s+\(([\d,.]+)x\)', result.stdout)
    t1_match = re.search(r'Strategy T\+1:\s+\$[\d,]+\.\d+\s+\(([\d,.]+)x\)', result.stdout)
    
    if t0_match and t1_match:
        expected_t0 = float(t0_match.group(1).replace(',', ''))
        expected_t1 = float(t1_match.group(1).replace(',', ''))
        
        actual_t0 = df_t0['Strategy_Cumulative'].iloc[-1] / df_t0['BH_Cumulative'].iloc[-1]
        actual_t1 = df_t1['Strategy_Cumulative'].iloc[-1] / df_t1['BH_Cumulative'].iloc[-1]
        
        print(f"T+0: {actual_t0:.2f}x (working code: {expected_t0:.2f}x) {'✓' if abs(actual_t0 - expected_t0) < 1 else '✗'}")
        print(f"T+1: {actual_t1:.2f}x (working code: {expected_t1:.2f}x) {'✓' if abs(actual_t1 - expected_t1) < 1 else '✗'}")
    else:
        print("✗ Could not extract values from working code")
        print("Working code output:")
        print(result.stdout[:500])
