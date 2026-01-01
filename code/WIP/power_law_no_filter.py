"""
Power Law Deviation Signal - NO 0.5% FILTER
Temporary version to see what happens without the hardcoded cutoff
"""
import pandas as pd
import numpy as np


def calculate_signal(df):
    """Calculate power law deviation signal WITHOUT the 0.5% filter"""
    df = df.copy()
    
    df['AbsReturn'] = np.abs(df['Return'])
    df['State'] = 'GREEN'
    
    window_days = 60
    
    for i in range(window_days, len(df)):
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
            continue
        
        log_x = np.log(sorted_returns[valid_mask][tail_mask])
        log_y = np.log(ccdf[valid_mask][tail_mask])
        slope, intercept = np.polyfit(log_x, log_y, 1)
        
        # Check today's return - REMOVED THE >= 0.5 FILTER
        today_abs_return = df.iloc[i]['AbsReturn']
        
        # Predict where this return should be on power law
        if today_abs_return > 0:  # Just avoid log(0)
            predicted_ccdf = np.exp(intercept) * today_abs_return ** slope
            
            # Where is it actually?
            actual_ccdf = (abs_returns_window >= today_abs_return).sum() / n
            
            # Set to RED if actual > predicted
            if actual_ccdf > predicted_ccdf:
                df.loc[i, 'State'] = 'RED'
    
    red_days = (df['State'] == 'RED').sum()
    green_days = (df['State'] == 'GREEN').sum()
    
    print(f"✓ Power law signal (NO 0.5% filter):")
    print(f"  RED: {red_days:,} days ({red_days/len(df)*100:.1f}%)")
    print(f"  GREEN: {green_days:,} days ({green_days/len(df)*100:.1f}%)")
    
    return df
