import sys
sys.path.append('code/data')
from load_data import load_asset
import numpy as np
import pandas as pd

def calculate_alpha(returns, min_return=0.5, min_points=5):
    """Calculate power law alpha from returns"""
    sorted_returns = np.sort(np.abs(returns))[::-1]
    n = len(sorted_returns)
    ccdf = np.arange(1, n+1) / n
    valid_mask = (sorted_returns > 0) & (ccdf > 0)
    tail_mask = sorted_returns[valid_mask] > min_return
    if tail_mask.sum() < min_points:
        return None, None, None, None
    x = sorted_returns[valid_mask][tail_mask]
    y = ccdf[valid_mask][tail_mask]
    log_x = np.log(x)
    log_y = np.log(y)
    slope, intercept = np.polyfit(log_x, log_y, 1)
    alpha = -slope
    return x, y, alpha, intercept

def calculate_mean_deviation_series(df, window=60):
    """Calculate mean CCDF deviation for each day"""
    mean_deviations = []
    for i in range(len(df)):
        if i < window:
            mean_deviations.append(np.nan)
        else:
            returns = df.iloc[i-window:i]['Return'].values
            x, y, alpha, intercept = calculate_alpha(returns)
            
            if alpha is not None:
                power_law_fit = np.exp(intercept) * (x ** (-alpha))
                deviation = y - power_law_fit
                mask = (x >= 0.5) & (x <= 3.0)
                if mask.sum() > 0:
                    mean_dev = np.mean(deviation[mask])
                    mean_deviations.append(mean_dev)
                else:
                    mean_deviations.append(np.nan)
            else:
                mean_deviations.append(np.nan)
    return mean_deviations

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

# Load SPX and calculate mean deviation
print("Loading SPX and calculating mean deviation...")
df = load_asset('_spx_d.csv')
df['Mean_Deviation'] = calculate_mean_deviation_series(df)

# Identify drawdowns
drawdowns = identify_unique_drawdowns(df, threshold_pct=15)
exogenous = ['1987', '2020']
endogenous_dd = [dd for dd in drawdowns if not any(yr in dd['peak_date'].strftime('%Y') for yr in exogenous)]

print(f"\nAnalyzing {len(endogenous_dd)} endogenous drawdowns")
print("\nHypothesis: Before crashes, market spends MORE time in negative deviation")
print("(More time deviating from its own power law = tail risk building)\n")

lead_time = 126  # 6 months
results = []

for dd in endogenous_dd:
    peak_idx = dd['peak_idx']
    
    if peak_idx < lead_time * 2:
        continue
    
    # Calculate % time in negative deviation
    leadup_deviations = df.iloc[peak_idx - lead_time:peak_idx]['Mean_Deviation'].values
    normal_deviations = df.iloc[peak_idx - lead_time * 2:peak_idx - lead_time]['Mean_Deviation'].values
    
    # Remove NaNs
    leadup_deviations = leadup_deviations[~np.isnan(leadup_deviations)]
    normal_deviations = normal_deviations[~np.isnan(normal_deviations)]
    
    if len(leadup_deviations) == 0 or len(normal_deviations) == 0:
        continue
    
    # % of time negative
    leadup_pct_negative = (leadup_deviations < 0).sum() / len(leadup_deviations) * 100
    normal_pct_negative = (normal_deviations < 0).sum() / len(normal_deviations) * 100
    
    diff = leadup_pct_negative - normal_pct_negative
    
    results.append({
        'peak_date': dd['peak_date'],
        'drawdown': dd['drawdown_pct'],
        'leadup_pct_neg': leadup_pct_negative,
        'normal_pct_neg': normal_pct_negative,
        'diff': diff
    })

# Print results
for r in results:
    more_time = "MORE TIME ✓" if r['diff'] > 0 else "LESS TIME ✗"
    print(f"{r['peak_date'].strftime('%Y-%m-%d')}: {r['leadup_pct_neg']:.1f}% vs {r['normal_pct_neg']:.1f}% = {r['diff']:+.1f}% {more_time}")

# Summary
more_time_count = sum(1 for r in results if r['diff'] > 0)
print(f"\nSummary: {more_time_count}/{len(results)} ({more_time_count/len(results)*100:.0f}%) spent MORE time in negative deviation before crash")
print(f"Average difference: {np.mean([r['diff'] for r in results]):.1f}%")

