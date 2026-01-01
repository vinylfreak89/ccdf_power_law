"""
Alpha Derivative Z-Score Signal

Measures the chaos/stability of the power law exponent (alpha) by:
1. Calculating 42-day rolling alpha
2. Taking derivative of alpha (dα/dt)
3. Smoothing |dα/dt| with 84-day MA
4. Z-score normalizing against 2-year (504-day) baseline

Signal States:
- RED: Z-score < -1 (alpha derivative quieter than baseline - stability)
- ORANGE: -1 <= Z-score <= 1 (neutral)
- GREEN: Z-score > 1 (alpha derivative more chaotic than baseline)
"""
import pandas as pd
import numpy as np


def calculate_alpha(returns, min_return=0.5):
    """Calculate power law alpha from returns"""
    sorted_returns = np.sort(np.abs(returns))[::-1]
    n = len(sorted_returns)
    ccdf = np.arange(1, n+1) / n
    valid_mask = (sorted_returns > 0) & (ccdf > 0)
    tail_mask = sorted_returns[valid_mask] > min_return
    if tail_mask.sum() < 10:
        return None
    x = sorted_returns[valid_mask][tail_mask]
    y = ccdf[valid_mask][tail_mask]
    log_x = np.log(x)
    log_y = np.log(y)
    slope, intercept = np.polyfit(log_x, log_y, 1)
    alpha = -slope
    return alpha


def calculate_signal(df, alpha_window=42, ma_window=84, zscore_window=504):
    """
    Calculate alpha derivative z-score signal.
    
    Args:
        df: DataFrame with columns: Date, Close, Return
        alpha_window: Window for rolling alpha calculation (default 42)
        ma_window: Window for MA of |dα/dt| (default 84)
        zscore_window: Window for z-score normalization (default 504)
        
    Returns:
        DataFrame with State column added:
        - 'GREEN': Z-score > 1 (more chaotic)
        - 'ORANGE': -1 <= Z-score <= 1 (neutral)
        - 'RED': Z-score < -1 (quieter/stable)
    """
    df = df.copy()
    
    # Calculate rolling alpha on full dataframe
    df['Alpha'] = np.nan
    for i in range(alpha_window, len(df)):
        alpha = calculate_alpha(df.iloc[i-alpha_window:i]['Return'].values)
        if alpha is not None:
            df.iloc[i, df.columns.get_loc('Alpha')] = alpha
    
    # Work on clean subset for derivative and zscore calculations
    df_clean = df[df['Alpha'].notna()].copy().reset_index(drop=True)
    
    # Calculate derivative on clean data
    df_clean['Alpha_derivative'] = df_clean['Alpha'].diff()
    df_clean['Abs_Derivative'] = df_clean['Alpha_derivative'].abs()
    df_clean['Abs_Derivative_MA'] = df_clean['Abs_Derivative'].rolling(window=ma_window).mean()
    
    # Z-score normalization on clean data
    df_clean['MA_Mean'] = df_clean['Abs_Derivative_MA'].rolling(window=zscore_window).mean()
    df_clean['MA_Std'] = df_clean['Abs_Derivative_MA'].rolling(window=zscore_window).std()
    df_clean['ZScore'] = (df_clean['Abs_Derivative_MA'] - df_clean['MA_Mean']) / df_clean['MA_Std']
    
    # Assign states on clean data
    df_clean['State'] = 'ORANGE'
    df_clean.loc[df_clean['ZScore'] > 1, 'State'] = 'GREEN'
    df_clean.loc[df_clean['ZScore'] < -1, 'State'] = 'RED'
    
    # Map states back to original dataframe using Date
    df['State'] = 'ORANGE'  # Default for rows without Alpha
    date_to_state = dict(zip(df_clean['Date'], df_clean['State']))
    df['State'] = df['Date'].map(date_to_state).fillna('ORANGE')
    
    # Print summary
    red_days = (df['State'] == 'RED').sum()
    orange_days = (df['State'] == 'ORANGE').sum()
    green_days = (df['State'] == 'GREEN').sum()
    
    print(f"✓ Alpha derivative z-score signal calculated:")
    print(f"  RED: {red_days:,} days ({red_days/len(df)*100:.1f}%)")
    print(f"  ORANGE: {orange_days:,} days ({orange_days/len(df)*100:.1f}%)")
    print(f"  GREEN: {green_days:,} days ({green_days/len(df)*100:.1f}%)")
    
    return df


if __name__ == '__main__':
    import sys
    sys.path.append('../data')
    from load_data import load_asset
    
    print("Running alpha derivative z-score signal on SPX...")
    df = load_asset('_spx_d.csv', min_date='1920-01-01')
    df = calculate_signal(df)
