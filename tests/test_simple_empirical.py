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
    """
    For each day in period, compare actual vs predicted CCDF
    Returns average gap across all days and thresholds
    """
    gaps = []
    
    for i in range(start_idx, end_idx):
        if i < 60:
            continue
            
        # Fit power law to last 60 days
        returns = df.iloc[i-60:i]['Return'].values
        alpha, intercept = calculate_alpha(returns)
        
        if alpha is None:
            continue
        
        # For each threshold, compare actual vs predicted
        abs_returns = np.abs(returns)
        for threshold in thresholds:
            # Actual: what % of last 60 days had |return| >= threshold
            actual_pct = (abs_returns >= threshold).sum() / len(abs_returns)
            
            # Predicted: what does power law say
            predicted_pct = np.exp(intercept) * (threshold ** (-alpha))
            
            # Gap (negative = fewer than expected)
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

# Load SPX
print("Loading SPX...")
df = load_asset('_spx_d.csv')

# Identify drawdowns
drawdowns = identify_unique_drawdowns(df, threshold_pct=15)
exogenous = ['1987', '2020']
endogenous_dd = [dd for dd in drawdowns if not any(yr in dd['peak_date'].strftime('%Y') for yr in exogenous)]

print(f"\nAnalyzing {len(endogenous_dd)} endogenous drawdowns")
print("\nHypothesis: Before crashes, actual < predicted (fewer moves than power law expects)")
print("Measuring: Average gap (Actual CCDF - Predicted CCDF) across 0.5-2% thresholds\n")

lead_time = 126
results = []

for dd in endogenous_dd:
    peak_idx = dd['peak_idx']
    
    if peak_idx < lead_time * 2:
        continue
    
    # Measure actual vs predicted for both periods
    leadup_gap = measure_actual_vs_predicted(df, peak_idx - lead_time, peak_idx)
    normal_gap = measure_actual_vs_predicted(df, peak_idx - lead_time * 2, peak_idx - lead_time)
    
    if np.isnan(leadup_gap) or np.isnan(normal_gap):
        continue
    
    results.append({
        'peak_date': dd['peak_date'],
        'drawdown': dd['drawdown_pct'],
        'leadup_gap': leadup_gap,
        'normal_gap': normal_gap,
        'diff': leadup_gap - normal_gap
    })

# Print results
for r in results:
    more_compressed = "MORE COMPRESSED ✓" if r['leadup_gap'] < r['normal_gap'] else "LESS COMPRESSED ✗"
    print(f"{r['peak_date'].strftime('%Y-%m-%d')}: {r['leadup_gap']:.4f} vs {r['normal_gap']:.4f} = {r['diff']:+.4f} {more_compressed}")

# Summary
compressed_count = sum(1 for r in results if r['diff'] < 0)
print(f"\nSummary: {compressed_count}/{len(results)} ({compressed_count/len(results)*100:.0f}%) were MORE compressed before crash")
print(f"Average gap difference: {np.mean([r['diff'] for r in results]):.4f}")

