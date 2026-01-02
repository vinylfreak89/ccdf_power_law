import sys
sys.path.append('code/data')
from load_data import load_asset
import numpy as np
import pandas as pd

def calculate_alpha(returns, min_return=0.5, min_points=5):
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

def analyze_random_periods(filename, asset_name, n_samples=20, seed=42):
    print(f"\nAnalyzing {asset_name}...")
    df = load_asset(filename)
    
    np.random.seed(seed)
    lead_time = 126
    
    # Pick random indices that have enough history
    valid_indices = range(lead_time * 2, len(df) - lead_time)
    if len(valid_indices) < n_samples:
        n_samples = len(valid_indices)
    
    random_indices = np.random.choice(valid_indices, size=n_samples, replace=False)
    
    results = []
    for idx in random_indices:
        leadup_gap = measure_actual_vs_predicted(df, idx - lead_time, idx)
        normal_gap = measure_actual_vs_predicted(df, idx - lead_time * 2, idx - lead_time)
        
        if np.isnan(leadup_gap) or np.isnan(normal_gap):
            continue
        
        results.append({
            'Asset': asset_name,
            'Date': df.iloc[idx]['Date'].strftime('%Y-%m-%d'),
            'Lead-up Gap': f"{leadup_gap:.4f}",
            'Normal Gap': f"{normal_gap:.4f}",
            'Difference': f"{leadup_gap - normal_gap:.4f}",
            'Compressed?': '✓' if leadup_gap < normal_gap else '✗'
        })
    
    if len(results) > 0:
        return pd.DataFrame(results)
    return pd.DataFrame()

# Test on same assets
assets = [
    ('_spx_d.csv', 'SPX'),
    ('_ndx_d.csv', 'NDX'),
    ('nvda_us_d.csv', 'NVDA'),
    ('btc_v_d.csv', 'BTC'),
    ('xauusd_d.csv', 'GOLD'),
    ('tlt_us_d.csv', 'TLT'),
]

all_results = []
for filename, name in assets:
    result = analyze_random_periods(filename, name, n_samples=20)
    if len(result) > 0:
        all_results.append(result)

if len(all_results) > 0:
    combined = pd.concat(all_results, ignore_index=True)
    
    # Summary
    print("\n" + "="*80)
    print("COMPRESSION IN RANDOM PERIODS - SUMMARY")
    print("="*80)
    
    for asset in combined['Asset'].unique():
        asset_data = combined[combined['Asset'] == asset]
        compressed = (asset_data['Compressed?'] == '✓').sum()
        total = len(asset_data)
        print(f"{asset:6s}: {compressed}/{total} ({compressed/total*100:.0f}%)")
    
    total_compressed = (combined['Compressed?'] == '✓').sum()
    total = len(combined)
    print(f"\nOVERALL: {total_compressed}/{total} ({total_compressed/total*100:.0f}%) random periods show compression")
    
    print("\n" + "="*80)
    print("COMPARISON:")
    print("="*80)
    print("Before CRASHES (SPX):  81% compressed")
    print("Before RALLIES (SPX):  86% compressed")
    print(f"RANDOM periods (SPX):  {(combined[combined['Asset']=='SPX']['Compressed?']=='✓').sum()}/{len(combined[combined['Asset']=='SPX'])} ({(combined[combined['Asset']=='SPX']['Compressed?']=='✓').sum()/len(combined[combined['Asset']=='SPX'])*100:.0f}%) compressed")
    
    combined.to_csv('/mnt/user-data/outputs/random_compression_test.csv', index=False)
    print("\n✓ Saved to random_compression_test.csv")

