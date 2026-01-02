import sys
sys.path.append('code/data')
from load_data import load_asset
import numpy as np
import pandas as pd

def calculate_alpha(returns, min_return=0.5, min_points=5):
    """Calculate power law alpha"""
    sorted_returns = np.sort(np.abs(returns))[::-1]
    n = len(sorted_returns)
    ccdf = np.arange(1, n+1) / n
    valid_mask = (sorted_returns > 0) & (ccdf > 0)
    tail_mask = sorted_returns[valid_mask] > min_return
    if tail_mask.sum() < min_points:
        return None, None
    x = sorted_returns[valid_mask][tail_mask]
    y = ccdf[valid_mask][tail_mask]
    log_x = np.log(x)
    log_y = np.log(y)
    slope, intercept = np.polyfit(log_x, log_y, 1)
    return -slope, intercept

def measure_actual_vs_predicted(df, start_idx, end_idx, thresholds=[0.5, 1.0, 1.5, 2.0]):
    """For each day in period, compare actual vs predicted CCDF"""
    gaps = []
    
    for i in range(start_idx, end_idx):
        if i < 60:
            continue
            
        returns = df.iloc[i-60:i]['Return'].values
        alpha, intercept = calculate_alpha(returns)
        
        if alpha is None:
            continue
        
        abs_returns = np.abs(returns)
        for threshold in thresholds:
            actual_pct = (abs_returns >= threshold).sum() / len(abs_returns)
            predicted_pct = np.exp(intercept) * (threshold ** (-alpha))
            gap = actual_pct - predicted_pct
            gaps.append(gap)
    
    return np.mean(gaps) if len(gaps) > 0 else np.nan

def identify_unique_drawdowns(df, threshold_pct=15):
    """Identify drawdowns"""
    df['Running_Max'] = df['Close'].expanding().max()
    df['Drawdown'] = (df['Close'] - df['Running_Max']) / df['Running_Max'] * 100
    
    troughs = []
    i = 0
    while i < len(df):
        if df.iloc[i]['Drawdown'] <= -threshold_pct:
            start = i
            while i < len(df) and df.iloc[i]['Drawdown'] <= -threshold_pct * 0.5:
                i += 1
            
            trough_window = df.iloc[start:i+1]
            trough_idx = trough_window['Drawdown'].idxmin()
            peak_window = df.iloc[max(0, trough_idx-756):trough_idx]
            peak_idx = peak_window['Close'].idxmax()
            
            troughs.append({
                'peak_date': df.iloc[peak_idx]['Date'],
                'trough_date': df.iloc[trough_idx]['Date'],
                'drawdown_pct': df.iloc[trough_idx]['Drawdown'],
                'peak_idx': peak_idx,
                'trough_idx': trough_idx
            })
        i += 1
    
    seen_troughs = set()
    unique = []
    for dd in troughs:
        if dd['trough_idx'] not in seen_troughs:
            unique.append(dd)
            seen_troughs.add(dd['trough_idx'])
    
    return unique

# Load and process
df = load_asset('_spx_d.csv')
drawdowns = identify_unique_drawdowns(df, threshold_pct=15)
exogenous = ['1987', '2020']
endogenous_dd = [dd for dd in drawdowns if not any(yr in dd['peak_date'].strftime('%Y') for yr in exogenous)]

lead_time = 126
results = []

for dd in endogenous_dd:
    peak_idx = dd['peak_idx']
    
    if peak_idx < lead_time * 2:
        continue
    
    leadup_gap = measure_actual_vs_predicted(df, peak_idx - lead_time, peak_idx)
    normal_gap = measure_actual_vs_predicted(df, peak_idx - lead_time * 2, peak_idx - lead_time)
    
    if np.isnan(leadup_gap) or np.isnan(normal_gap):
        continue
    
    results.append({
        'Peak Date': dd['peak_date'].strftime('%Y-%m-%d'),
        'Drawdown %': f"{dd['drawdown_pct']:.1f}",
        'Lead-up Gap': f"{leadup_gap:.4f}",
        'Normal Gap': f"{normal_gap:.4f}",
        'Difference': f"{leadup_gap - normal_gap:.4f}",
        'Compressed?': '✓' if leadup_gap < normal_gap else '✗'
    })

# Create DataFrame and print
results_df = pd.DataFrame(results)
print("\nEmpirical Test Results: Actual vs Predicted CCDF Gap")
print("=" * 90)
print(results_df.to_string(index=False))
print("=" * 90)
print(f"\nCompressed before crash: {(results_df['Compressed?'] == '✓').sum()}/{len(results_df)} ({(results_df['Compressed?'] == '✓').sum()/len(results_df)*100:.0f}%)")

# Save to CSV
results_df.to_csv('/mnt/user-data/outputs/compression_test_results.csv', index=False)
print("\n✓ Saved to compression_test_results.csv")

