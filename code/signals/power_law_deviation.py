"""
Power Law Deviation Signal Calculator

NOT YET REFINED: Works well on SPX but needs tuning for other assets.
Uses 60-day rolling window to detect when returns deviate from power law distribution.

Signal Logic:
1. Fit power law to last 60 days of returns (tail > 0.5%)
2. For today's return, compare actual CCDF vs predicted CCDF
3. If actual > predicted → Signal ON (more frequent than power law predicts)
4. If actual ≤ predicted → Signal OFF (normal distribution)

NOTE: This version does NOT include the 3-day lag filter.
"""
import pandas as pd
import numpy as np


def calculate_signal(df):
    """
    Calculate power law deviation signal using 60-day rolling window.
    
    Args:
        df: DataFrame with columns: Date, Close, Return
        
    Returns:
        DataFrame with added columns:
            - AbsReturn: Absolute value of returns
            - State: 'RED' (deviation detected) or 'GREEN' (normal)
    """
    df = df.copy()
    
    df['AbsReturn'] = np.abs(df['Return'])
    df['State'] = 'GREEN'  # Default to GREEN
    
    window_days = 60
    
    for i in range(window_days, len(df)):
        # Get last 60 days
        window_data = df.iloc[i-window_days:i].copy()
        abs_returns_window = np.abs(window_data['Return'].values)
        
        # Calculate CCDF for window
        sorted_returns = np.sort(abs_returns_window)[::-1]
        n = len(sorted_returns)
        ccdf = np.arange(1, n+1) / n
        
        # Fit power law to tail (returns > 0.5%)
        valid_mask = (sorted_returns > 0) & (ccdf > 0)
        tail_mask = sorted_returns[valid_mask] > 0.5
        
        if tail_mask.sum() < 10:
            # Not enough tail data to fit
            continue
        
        log_x = np.log(sorted_returns[valid_mask][tail_mask])
        log_y = np.log(ccdf[valid_mask][tail_mask])
        slope, intercept = np.polyfit(log_x, log_y, 1)
        
        # Check today's return
        today_abs_return = df.iloc[i]['AbsReturn']
        
        if today_abs_return >= 0.5:
            # Predict where this return should be on power law
            predicted_ccdf = np.exp(intercept) * today_abs_return ** slope
            
            # Where is it actually?
            actual_ccdf = (abs_returns_window >= today_abs_return).sum() / n
            
            # Set to RED if actual > predicted (more frequent than expected)
            if actual_ccdf > predicted_ccdf:
                df.loc[i, 'State'] = 'RED'
    
    red_days = (df['State'] == 'RED').sum()
    green_days = (df['State'] == 'GREEN').sum()
    red_pct = red_days / len(df) * 100
    green_pct = green_days / len(df) * 100
    
    print(f"✓ Power law deviation signal calculated:")
    print(f"  RED: {red_days:,} days ({red_pct:.1f}%)")
    print(f"  GREEN: {green_days:,} days ({green_pct:.1f}%)")
    print(f"  Valid from day {window_days} onwards")
    
    return df


if __name__ == '__main__':
    # Run the signal
    import sys
    sys.path.append('/mnt/user-data/outputs/code/data')
    from load_data import load_asset
    
    print("Running power law deviation signal on SPX...")
    df = load_asset('_spx_d.csv')
    df = calculate_signal(df)
