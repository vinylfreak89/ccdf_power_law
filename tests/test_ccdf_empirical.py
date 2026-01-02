import sys
sys.path.append('code/data')
from load_data import load_asset
import numpy as np
import pandas as pd

def identify_unique_drawdowns(df, threshold_pct=15):
    """Identify drawdowns, removing duplicates"""
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

def calculate_ccdf_at_thresholds(returns, thresholds):
    """Calculate CCDF values at specific threshold points"""
    abs_returns = np.abs(returns)
    n = len(abs_returns)
    
    ccdf_values = {}
    for threshold in thresholds:
        # P(|return| >= threshold)
        count = (abs_returns >= threshold).sum()
        ccdf_values[threshold] = count / n if n > 0 else 0
    
    return ccdf_values

# Load SPX
print("Loading SPX...")
df = load_asset('_spx_d.csv')

# Identify drawdowns
drawdowns = identify_unique_drawdowns(df, threshold_pct=15)

# Exclude exogenous shocks
exogenous = ['1987', '2020']
endogenous_dd = [dd for dd in drawdowns if not any(yr in dd['peak_date'].strftime('%Y') for yr in exogenous)]
print(f"Analyzing {len(endogenous_dd)} endogenous drawdowns\n")

# Test at multiple threshold points
thresholds = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
lead_time = 126  # 6 months

results = []
for dd in endogenous_dd:
    peak_idx = dd['peak_idx']
    
    if peak_idx < lead_time * 2:
        continue
    
    # Get returns for both periods
    leadup_returns = df.iloc[peak_idx - lead_time:peak_idx]['Return'].values
    normal_returns = df.iloc[peak_idx - lead_time * 2:peak_idx - lead_time]['Return'].values
    
    # Calculate CCDF at each threshold
    leadup_ccdf = calculate_ccdf_at_thresholds(leadup_returns, thresholds)
    normal_ccdf = calculate_ccdf_at_thresholds(normal_returns, thresholds)
    
    # Calculate mean deviation (average difference across thresholds)
    diffs = [leadup_ccdf[t] - normal_ccdf[t] for t in thresholds]
    mean_diff = np.mean(diffs)
    
    results.append({
        'peak_date': dd['peak_date'],
        'drawdown': dd['drawdown_pct'],
        'mean_ccdf_diff': mean_diff,
        'leadup_ccdf': leadup_ccdf,
        'normal_ccdf': normal_ccdf
    })

# Print results
print("Hypothesis: CCDF values LOWER before crash = quieter (fewer moves >= threshold)")
print("Mean CCDF diff = average across 0.5-3% thresholds")
print("(Negative = quieter before crash)\n")

for r in results:
    quieter = "QUIETER ✓" if r['mean_ccdf_diff'] < 0 else "NOISIER ✗"
    print(f"{r['peak_date'].strftime('%Y-%m-%d')}: {r['mean_ccdf_diff']:+.3f} {quieter}")
    
    # Show detail for a few
    if abs(r['mean_ccdf_diff']) > 0.05:
        print(f"  Detail: ", end='')
        for t in [0.5, 1.5, 3.0]:
            print(f"{t}%: {r['leadup_ccdf'][t]:.2f} vs {r['normal_ccdf'][t]:.2f}  ", end='')
        print()

# Summary
quieter_count = sum(1 for r in results if r['mean_ccdf_diff'] < 0)
print(f"\nSummary: {quieter_count}/{len(results)} ({quieter_count/len(results)*100:.0f}%) had lower CCDF before crash")

