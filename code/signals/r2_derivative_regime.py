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
        DataFrame with State column added:
        - 'GREEN': 2x long (R² improving - power law strengthening)
        - 'ORANGE': 1x long (neutral)
        - 'RED': short (R² degrading - power law weakening)
    """
    df = df.copy()
    
    # Calculate global alpha from full dataset
    global_alpha, _ = calculate_alpha_and_fit(df['Return'].values)
    
    # Calculate rolling R² using global alpha
    global_r2 = []
    for i in range(window, len(df)):
        r = calculate_fit_with_fixed_alpha(df.iloc[i-window:i]['Return'].values, global_alpha)
        global_r2.append(r if r is not None else np.nan)
    
    # Add to dataframe
    df['GlobalR2'] = [np.nan] * window + global_r2
    
    # Work on subset where GlobalR2 is not NaN (like original logic)
    df_subset = df[df['GlobalR2'].notna()].copy().reset_index(drop=True)
    
    # Calculate derivative
    df_subset['R2_derivative'] = df_subset['GlobalR2'].diff()
    
    # Calculate threshold
    derivative_clean = df_subset['R2_derivative'].dropna()
    std = derivative_clean.std()
    threshold_pos = threshold_sigma * std
    threshold_neg = -threshold_sigma * std
    
    # Find breach signals on the subset
    signals = []
    for i in range(len(df_subset)):
        deriv = df_subset.iloc[i]['R2_derivative']
        if pd.notna(deriv):
            if deriv > threshold_pos:
                signals.append((i, 'green'))
            elif deriv < threshold_neg:
                signals.append((i, 'red'))
    
    # Color regions between consecutive matching signals
    colored_regions = []
    for i in range(len(signals) - 1):
        start_idx, start_color = signals[i]
        end_idx, end_color = signals[i + 1]
        
        if start_color == end_color:
            colored_regions.append((start_idx, end_idx, start_color))
    
    # Create state array on the subset
    state_subset = ['orange'] * len(df_subset)
    for start_idx, end_idx, color in colored_regions:
        for j in range(start_idx, end_idx + 1):
            state_subset[j] = color
    
    df_subset['State'] = [s.upper() for s in state_subset]
    
    # Map back to original dataframe using Date
    df['State'] = 'ORANGE'  # Default for rows with NaN GlobalR2
    date_to_state = dict(zip(df_subset['Date'], df_subset['State']))
    df['State'] = df['Date'].map(date_to_state).fillna('ORANGE')
    
    # Print summary
    red_days = (df['State'] == 'RED').sum()
    orange_days = (df['State'] == 'ORANGE').sum()
    green_days = (df['State'] == 'GREEN').sum()
    
    print(f"✓ R² derivative signal calculated:")
    print(f"  RED: {red_days:,} days ({red_days/len(df)*100:.1f}%)")
    print(f"  ORANGE: {orange_days:,} days ({orange_days/len(df)*100:.1f}%)")
    print(f"  GREEN: {green_days:,} days ({green_days/len(df)*100:.1f}%)")
    
    return df
