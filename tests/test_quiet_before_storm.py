import sys
sys.path.append('code/data')
from load_data import load_asset
import numpy as np
import pandas as pd

def identify_unique_drawdowns(df, threshold_pct=15):
    """Identify drawdowns, removing duplicates"""
    df['Running_Max'] = df['Close'].expanding().max()
    df['Drawdown'] = (df['Close'] - df['Running_Max']) / df['Running_Max'] * 100
    
    # Find all troughs below threshold
    troughs = []
    i = 0
    while i < len(df):
        if df.iloc[i]['Drawdown'] <= -threshold_pct:
            # Find local minimum in this drawdown
            start = i
            while i < len(df) and df.iloc[i]['Drawdown'] <= -threshold_pct * 0.5:
                i += 1
            
            trough_window = df.iloc[start:i+1]
            trough_idx = trough_window['Drawdown'].idxmin()
            
            # Find peak before this trough
            peak_window = df.iloc[max(0, trough_idx-756):trough_idx]  # Look back up to 3 years
            peak_idx = peak_window['Close'].idxmax()
            
            troughs.append({
                'peak_date': df.iloc[peak_idx]['Date'],
                'trough_date': df.iloc[trough_idx]['Date'],
                'drawdown_pct': df.iloc[trough_idx]['Drawdown'],
                'peak_idx': peak_idx,
                'trough_idx': trough_idx
            })
        i += 1
    
    # Remove duplicates (same trough)
    seen_troughs = set()
    unique = []
    for dd in troughs:
        if dd['trough_idx'] not in seen_troughs:
            unique.append(dd)
            seen_troughs.add(dd['trough_idx'])
    
    return unique

def analyze_return_distribution(df, start_idx, end_idx):
    """Analyze return distribution in a period"""
    window = df.iloc[start_idx:end_idx]
    returns = np.abs(window['Return'].values)
    
    # Count moves in different ranges
    count_05_3 = ((returns >= 0.5) & (returns <= 3.0)).sum()
    count_over_3 = (returns > 3.0).sum()
    total_days = len(returns)
    
    return {
        'total_days': total_days,
        'count_05_3': count_05_3,
        'count_over_3': count_over_3,
        'pct_05_3': count_05_3 / total_days * 100 if total_days > 0 else 0,
        'pct_over_3': count_over_3 / total_days * 100 if total_days > 0 else 0,
        'mean_return': returns.mean(),
        'std_return': returns.std()
    }

# Load SPX
print("Loading SPX...")
df = load_asset('_spx_d.csv')

# Identify drawdowns
drawdowns = identify_unique_drawdowns(df, threshold_pct=15)
print(f"Found {len(drawdowns)} unique drawdowns >= 15%\n")

# Exclude exogenous shocks (1987 Black Monday, 2020 COVID)
exogenous = ['1987', '2020']
endogenous_dd = [dd for dd in drawdowns if not any(yr in dd['peak_date'].strftime('%Y') for yr in exogenous)]
print(f"After excluding 1987 and 2020: {len(endogenous_dd)} drawdowns\n")

# For each drawdown, analyze 6 months before peak
lead_time = 126  # ~6 months

results = []
for dd in endogenous_dd:
    peak_idx = dd['peak_idx']
    
    if peak_idx < lead_time:
        continue  # Not enough history
    
    # 6 months before peak
    leadup = analyze_return_distribution(df, peak_idx - lead_time, peak_idx)
    
    # Compare to "normal" period (12-6 months before peak)
    if peak_idx < lead_time * 2:
        continue
    normal = analyze_return_distribution(df, peak_idx - lead_time * 2, peak_idx - lead_time)
    
    results.append({
        'peak_date': dd['peak_date'],
        'drawdown': dd['drawdown_pct'],
        'leadup_pct_05_3': leadup['pct_05_3'],
        'normal_pct_05_3': normal['pct_05_3'],
        'diff': leadup['pct_05_3'] - normal['pct_05_3'],
        'leadup_std': leadup['std_return'],
        'normal_std': normal['std_return']
    })

# Print results
print("Hypothesis: 6mo before crash has FEWER 0.5-3% moves than 12-6mo before")
print("(Negative diff = quieter before crash)\n")

for r in results:
    quieter = "QUIETER ✓" if r['diff'] < 0 else "NOISIER ✗"
    print(f"{r['peak_date'].strftime('%Y-%m-%d')}: {r['leadup_pct_05_3']:.1f}% vs {r['normal_pct_05_3']:.1f}% = {r['diff']:+.1f}% {quieter}")

# Summary
quieter_count = sum(1 for r in results if r['diff'] < 0)
print(f"\nSummary: {quieter_count}/{len(results)} ({quieter_count/len(results)*100:.0f}%) were quieter before crash")

