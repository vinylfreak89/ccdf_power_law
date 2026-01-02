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

def identify_rallies(df, threshold_pct=10):
    """Identify rallies (inverse of drawdowns)"""
    df['Running_Min'] = df['Close'].expanding().min()
    df['Rally'] = (df['Close'] - df['Running_Min']) / df['Running_Min'] * 100
    
    rallies = []
    i = 0
    while i < len(df):
        if df.iloc[i]['Rally'] >= threshold_pct:
            start = i
            # Find where rally ends (pullback of 50%)
            while i < len(df) and df.iloc[i]['Rally'] >= threshold_pct * 0.5:
                i += 1
            
            rally_window = df.iloc[start:i+1]
            peak_idx = rally_window['Rally'].idxmax()
            
            # Find trough before this rally
            trough_window = df.iloc[max(0, peak_idx-756):peak_idx]
            trough_idx = trough_window['Close'].idxmin()
            
            rallies.append({
                'trough_date': df.iloc[trough_idx]['Date'],
                'peak_date': df.iloc[peak_idx]['Date'],
                'rally_pct': df.iloc[peak_idx]['Rally'],
                'trough_idx': trough_idx,
                'peak_idx': peak_idx
            })
        i += 1
    
    # Remove duplicates
    seen_peaks = set()
    unique = []
    for r in rallies:
        if r['peak_idx'] not in seen_peaks:
            unique.append(r)
            seen_peaks.add(r['peak_idx'])
    
    return unique

def analyze_asset(filename, asset_name):
    print(f"\nAnalyzing {asset_name}...")
    df = load_asset(filename)
    rallies = identify_rallies(df, threshold_pct=10)
    
    if len(rallies) == 0:
        print(f"  No rallies found")
        return pd.DataFrame()
    
    print(f"  Found {len(rallies)} rallies >= 10%")
    
    lead_time = 126
    results = []
    
    for rally in rallies:
        trough_idx = rally['trough_idx']
        
        if trough_idx < lead_time * 2:
            continue
        
        leadup_gap = measure_actual_vs_predicted(df, trough_idx - lead_time, trough_idx)
        normal_gap = measure_actual_vs_predicted(df, trough_idx - lead_time * 2, trough_idx - lead_time)
        
        if np.isnan(leadup_gap) or np.isnan(normal_gap):
            continue
        
        results.append({
            'Asset': asset_name,
            'Trough Date': rally['trough_date'].strftime('%Y-%m-%d'),
            'Rally %': f"{rally['rally_pct']:.1f}",
            'Lead-up Gap': f"{leadup_gap:.4f}",
            'Normal Gap': f"{normal_gap:.4f}",
            'Difference': f"{leadup_gap - normal_gap:.4f}",
            'Compressed?': '✓' if leadup_gap < normal_gap else '✗'
        })
    
    if len(results) > 0:
        return pd.DataFrame(results)
    return pd.DataFrame()

# Test on key assets
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
    result = analyze_asset(filename, name)
    if len(result) > 0:
        all_results.append(result)

if len(all_results) > 0:
    combined = pd.concat(all_results, ignore_index=True)
    
    # Summary by asset
    print("\n" + "="*80)
    print("COMPRESSION BEFORE RALLIES - SUMMARY")
    print("="*80)
    
    for asset in combined['Asset'].unique():
        asset_data = combined[combined['Asset'] == asset]
        compressed = (asset_data['Compressed?'] == '✓').sum()
        total = len(asset_data)
        print(f"{asset:6s}: {compressed}/{total} ({compressed/total*100:.0f}%)")
    
    total_compressed = (combined['Compressed?'] == '✓').sum()
    total = len(combined)
    print(f"\nOVERALL: {total_compressed}/{total} ({total_compressed/total*100:.0f}%) rallies preceded by compression")
    
    combined.to_csv('/mnt/user-data/outputs/rally_compression_test.csv', index=False)
    print("\n✓ Saved to rally_compression_test.csv")

