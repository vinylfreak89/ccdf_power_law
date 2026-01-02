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

def analyze_all_periods(filename, asset_name):
    print(f"\nAnalyzing {asset_name}...")
    df = load_asset(filename)
    
    lead_time = 126  # 6 months
    forward_time = 126  # 6 months forward
    
    results = []
    
    # Test every valid period (every 20 days to keep it manageable)
    for idx in range(lead_time * 2, len(df) - forward_time, 20):
        # Measure compression
        leadup_gap = measure_actual_vs_predicted(df, idx - lead_time, idx)
        normal_gap = measure_actual_vs_predicted(df, idx - lead_time * 2, idx - lead_time)
        
        if np.isnan(leadup_gap) or np.isnan(normal_gap):
            continue
        
        is_compressed = leadup_gap < normal_gap
        
        # Measure what happened in 6 months BEFORE this period
        past_return = (df.iloc[idx]['Close'] - df.iloc[idx - lead_time]['Close']) / df.iloc[idx - lead_time]['Close'] * 100
        
        # Measure what happened in 6 months AFTER this period  
        future_return = (df.iloc[idx + forward_time]['Close'] - df.iloc[idx]['Close']) / df.iloc[idx]['Close'] * 100
        
        # Determine if reversal or continuation
        past_up = past_return > 0
        future_up = future_return > 0
        is_reversal = past_up != future_up
        
        results.append({
            'Asset': asset_name,
            'Date': df.iloc[idx]['Date'].strftime('%Y-%m-%d'),
            'Compressed': is_compressed,
            'Past_Return': past_return,
            'Future_Return': future_return,
            'Past_Direction': 'UP' if past_up else 'DOWN',
            'Future_Direction': 'UP' if future_up else 'DOWN',
            'Reversal': is_reversal
        })
    
    print(f"  Analyzed {len(results)} periods")
    return pd.DataFrame(results)

# Test on SPX first
result = analyze_all_periods('_spx_d.csv', 'SPX')

if len(result) > 0:
    # Analysis: Does compression predict reversals?
    print("\n" + "="*80)
    print("COMPRESSION vs DIRECTION ANALYSIS")
    print("="*80)
    
    compressed = result[result['Compressed'] == True]
    not_compressed = result[result['Compressed'] == False]
    
    print(f"\nWhen COMPRESSED (n={len(compressed)}):")
    print(f"  Reversals: {compressed['Reversal'].sum()} ({compressed['Reversal'].sum()/len(compressed)*100:.1f}%)")
    print(f"  Continuations: {(~compressed['Reversal']).sum()} ({(~compressed['Reversal']).sum()/len(compressed)*100:.1f}%)")
    
    print(f"\nWhen NOT compressed (n={len(not_compressed)}):")
    print(f"  Reversals: {not_compressed['Reversal'].sum()} ({not_compressed['Reversal'].sum()/len(not_compressed)*100:.1f}%)")
    print(f"  Continuations: {(~not_compressed['Reversal']).sum()} ({(~not_compressed['Reversal']).sum()/len(not_compressed)*100:.1f}%)")
    
    # Break down by past direction
    print("\n" + "="*80)
    print("AFTER DOWN PERIODS:")
    print("="*80)
    after_down = result[result['Past_Direction'] == 'DOWN']
    after_down_compressed = after_down[after_down['Compressed'] == True]
    after_down_not_compressed = after_down[after_down['Compressed'] == False]
    
    print(f"\nCompressed after down (n={len(after_down_compressed)}):")
    rallied = (after_down_compressed['Future_Direction'] == 'UP').sum()
    print(f"  Rallied: {rallied} ({rallied/len(after_down_compressed)*100:.1f}%)")
    print(f"  Continued down: {len(after_down_compressed) - rallied} ({(len(after_down_compressed)-rallied)/len(after_down_compressed)*100:.1f}%)")
    
    print(f"\nNot compressed after down (n={len(after_down_not_compressed)}):")
    rallied = (after_down_not_compressed['Future_Direction'] == 'UP').sum()
    print(f"  Rallied: {rallied} ({rallied/len(after_down_not_compressed)*100:.1f}%)")
    print(f"  Continued down: {len(after_down_not_compressed) - rallied} ({(len(after_down_not_compressed)-rallied)/len(after_down_not_compressed)*100:.1f}%)")
    
    print("\n" + "="*80)
    print("AFTER UP PERIODS:")
    print("="*80)
    after_up = result[result['Past_Direction'] == 'UP']
    after_up_compressed = after_up[after_up['Compressed'] == True]
    after_up_not_compressed = after_up[after_up['Compressed'] == False]
    
    print(f"\nCompressed after up (n={len(after_up_compressed)}):")
    crashed = (after_up_compressed['Future_Direction'] == 'DOWN').sum()
    print(f"  Crashed: {crashed} ({crashed/len(after_up_compressed)*100:.1f}%)")
    print(f"  Continued up: {len(after_up_compressed) - crashed} ({(len(after_up_compressed)-crashed)/len(after_up_compressed)*100:.1f}%)")
    
    print(f"\nNot compressed after up (n={len(after_up_not_compressed)}):")
    crashed = (after_up_not_compressed['Future_Direction'] == 'DOWN').sum()
    print(f"  Crashed: {crashed} ({crashed/len(after_up_not_compressed)*100:.1f}%)")
    print(f"  Continued up: {len(after_up_not_compressed) - crashed} ({(len(after_up_not_compressed)-crashed)/len(after_up_not_compressed)*100:.1f}%)")
    
    result.to_csv('/mnt/user-data/outputs/directional_analysis_spx.csv', index=False)
    print("\n✓ Saved to directional_analysis_spx.csv")

