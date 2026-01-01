"""
R² Derivative Regime Signal

Signal based on global power law fit quality derivative.

Logic:
- Breach +1σ → GREEN regime (fit improving)
- Breach -1σ → RED regime (fit degrading)
- Consecutive matching signals validate the regime
- Signal flips invalidate → WHITE (neutral)

Strategy:
- WHITE: Long (1x)
- RED: Short (-1x)
- GREEN: 2x Long (2x)
"""
import pandas as pd
import numpy as np


def calculate_alpha_and_fit(returns, min_return=0.5):
    """Calculate alpha and R² for a set of returns"""
    sorted_returns = np.sort(np.abs(returns))[::-1]
    n = len(sorted_returns)
    ccdf = np.arange(1, n+1) / n
    
    valid_mask = (sorted_returns > 0) & (ccdf > 0)
    tail_mask = sorted_returns[valid_mask] > min_return
    
    if tail_mask.sum() < 10:
        return None, None
    
    x = sorted_returns[valid_mask][tail_mask]
    y = ccdf[valid_mask][tail_mask]
    
    log_x = np.log(x)
    log_y = np.log(y)
    slope, intercept = np.polyfit(log_x, log_y, 1)
    alpha = -slope
    
    predicted_log_y = slope * log_x + intercept
    ss_res = np.sum((log_y - predicted_log_y) ** 2)
    ss_tot = np.sum((log_y - np.mean(log_y)) ** 2)
    r_squared = 1 - (ss_res / ss_tot)
    
    return alpha, r_squared


def calculate_fit_with_fixed_alpha(returns, fixed_alpha, min_return=0.5):
    """Calculate R² using a fixed alpha"""
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
    
    slope = -fixed_alpha
    intercept = np.mean(log_y - slope * log_x)
    
    predicted_log_y = slope * log_x + intercept
    ss_res = np.sum((log_y - predicted_log_y) ** 2)
    ss_tot = np.sum((log_y - np.mean(log_y)) ** 2)
    r_squared = 1 - (ss_res / ss_tot)
    
    return r_squared


def generate_signal(df, window=21, threshold_sigma=1.0):
    """
    Generate R² derivative regime signal.
    
    Args:
        df: DataFrame with Return column
        window: Rolling window for alpha calculation
        threshold_sigma: Threshold in standard deviations (default 1.0)
        
    Returns:
        DataFrame with Signal column:
        - 2.0 = GREEN (2x long)
        - 1.0 = WHITE (1x long)
        - -1.0 = RED (short)
    """
    # Calculate global alpha from full dataset
    global_alpha, _ = calculate_alpha_and_fit(df['Return'].values)
    
    # Calculate rolling R² using global alpha
    global_r2 = []
    for i in range(window, len(df)):
        r = calculate_fit_with_fixed_alpha(df.iloc[i-window:i]['Return'].values, global_alpha)
        global_r2.append(r if r is not None else np.nan)
    
    # Add to dataframe
    df = df.copy()
    df['GlobalR2'] = [np.nan] * window + global_r2
    
    # DROP NaN and RESET index (critical - indices must match signal finding!)
    df = df[df['GlobalR2'].notna()].copy().reset_index(drop=True)
    
    # Calculate derivative
    df['R2_derivative'] = df['GlobalR2'].diff()
    
    # Calculate threshold
    derivative_clean = df['R2_derivative'].dropna()
    std = derivative_clean.std()
    threshold_pos = threshold_sigma * std
    threshold_neg = -threshold_sigma * std
    
    # Find breach signals
    signals = []
    for i in range(len(df)):
        deriv = df.iloc[i]['R2_derivative']
        if pd.notna(deriv):
            if deriv > threshold_pos:
                signals.append((i, 'green'))
            elif deriv < threshold_neg:
                signals.append((i, 'red'))
    
    # Initialize all as white (neutral)
    regime = ['white'] * len(df)
    
    # Color regions between consecutive matching signals
    # Store as (start, end, color) where end is INCLUSIVE
    colored_regions = []
    for i in range(len(signals) - 1):
        start_idx, start_color = signals[i]
        end_idx, end_color = signals[i + 1]
        
        # Only color if consecutive signals match
        if start_color == end_color:
            colored_regions.append((start_idx, end_idx, start_color))
    
    # Now color the regions (end is INCLUSIVE like manual plot)
    regime = ['white'] * len(df)
    for start_idx, end_idx, color in colored_regions:
        for j in range(start_idx, end_idx + 1):
            regime[j] = color
    
    df['Regime'] = regime
    
    # Convert to signal
    # WHITE = 1.0 (long)
    # GREEN = 2.0 (2x long)
    # RED = -1.0 (short)
    df['Signal'] = df['Regime'].map({
        'white': 1.0,
        'green': 2.0,
        'red': -1.0
    })
    
    return df[['Date', 'Signal']].copy()
